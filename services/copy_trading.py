# PolyScore — Copy Trading Service
# Мониторит трейдеров и автоматически копирует их сделки

import asyncio
import aiohttp
from typing import Optional
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import POLY_API_KEY
from services.database import (
    get_all_followed_traders,
    update_last_seen_trade,
    get_last_seen_trade,
)
from services.polymarket import clob


# ══════════════════════════════════════════════════════════════════════
# Copy Trading Service
# ══════════════════════════════════════════════════════════════════════

class CopyTradingService:
    """
    Сервис для копирования сделок.
    Опрашивает публичный API Polymarket для новых сделок трейдеров.
    Затем исполняет пропорциональные копии для подписчиков.
    """

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.monitoring = False
        self.callbacks = []  # list[async callable] для уведомлений в бот

    async def _get_session(self) -> aiohttp.ClientSession:
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    def on_trade_executed(self, callback):
        """Зарегистрировать callback для уведомления о скопированной сделке."""
        self.callbacks.append(callback)

    async def _notify_callbacks(self, event: dict):
        """Отправить уведомления в зарегистрированные callbacks."""
        for cb in self.callbacks:
            try:
                await cb(event)
            except Exception as e:
                print(f"[CopyTrading] Callback error: {e}")

    # ─────────────────────────────────────────────────────────────────────
    # 1. Опрос трейдера за новыми сделками
    # ─────────────────────────────────────────────────────────────────────

    async def poll_trader(self, trader_address: str) -> list[dict]:
        """
        Получить последние сделки трейдера из публичного API.

        GET https://data-api.polymarket.com/trades?user={address}&limit=10

        Возвращает список новых сделок (после last_trade_id).
        """
        if not trader_address:
            return []

        session = await self._get_session()
        url = f"https://data-api.polymarket.com/trades"
        params = {
            "user": trader_address,
            "limit": 10,
        }

        try:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    trades = await resp.json()
                    if not isinstance(trades, list):
                        trades = trades.get("trades", [])
                    return trades
        except asyncio.TimeoutError:
            print(f"[CopyTrading] Timeout polling {trader_address}")
        except Exception as e:
            print(f"[CopyTrading] Error polling {trader_address}: {e}")

        return []

    # ─────────────────────────────────────────────────────────────────────
    # 2. Получение позиций трейдера (для определения размера сделки)
    # ─────────────────────────────────────────────────────────────────────

    async def get_trader_positions(self, trader_address: str) -> list[dict]:
        """
        Получить текущие позиции трейдера.

        GET https://data-api.polymarket.com/positions?user={address}
        """
        if not trader_address:
            return []

        session = await self._get_session()
        url = f"https://data-api.polymarket.com/positions"
        params = {"user": trader_address}

        try:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    positions = await resp.json()
                    if not isinstance(positions, list):
                        positions = positions.get("positions", [])
                    return positions
        except Exception as e:
            print(f"[CopyTrading] Error getting positions for {trader_address}: {e}")

        return []

    # ─────────────────────────────────────────────────────────────────────
    # 3. Расчёт пропорционального размера копии
    # ─────────────────────────────────────────────────────────────────────

    def calculate_copy_size(
        self,
        follower_balance: float,
        trade_size: float,
        trader_total_value: float,
        copy_pct: float,
    ) -> float:
        """
        Рассчитать размер копии.

        Формула:
            copy_size = follower_balance * (trade_size / trader_total_value) * copy_pct / 100

        Пример:
        - follower_balance = 1000 USDC
        - trade_size = 50 USDC (сделка трейдера)
        - trader_total_value = 500 USDC (общий портфель трейдера)
        - copy_pct = 25

        copy_size = 1000 * (50/500) * 25/100 = 1000 * 0.1 * 0.25 = 25 USDC
        """
        if trader_total_value <= 0:
            return 0.0

        ratio = trade_size / trader_total_value
        copy_size = follower_balance * ratio * (copy_pct / 100.0)
        return max(copy_size, 0.0)

    # ─────────────────────────────────────────────────────────────────────
    # 4. Исполнение копии сделки
    # ─────────────────────────────────────────────────────────────────────

    async def execute_copy_trade(
        self,
        trade: dict,
        follower_user_id: int,
        follower_wallet: str,
        copy_pct: float,
        trader_address: str,
    ) -> bool:
        """
        Исполнить копию сделки для последователя.

        Args:
            trade: dict с market_id, token_id, side, size
            follower_user_id: ID пользователя в Telegram
            follower_wallet: адрес кошелька последователя
            copy_pct: процент копирования (1–100)
            trader_address: адрес трейдера (для логирования)

        Returns:
            True если сделка исполнена, False если ошибка
        """
        if not POLY_API_KEY:
            print(f"[CopyTrading] User {follower_user_id} has no wallet configured")
            return False

        try:
            # Получить данные для расчёта размера
            follower_balance = await clob.get_balance(follower_wallet)
            trader_positions = await self.get_trader_positions(trader_address)

            if not trader_positions:
                print(f"[CopyTrading] Could not get trader positions for {trader_address}")
                return False

            # Рассчитать общую стоимость портфеля трейдера
            trader_total_value = sum(float(p.get("size", 0)) for p in trader_positions)

            if trader_total_value <= 0:
                print(f"[CopyTrading] Trader {trader_address} has no value in positions")
                return False

            # Размер оригинальной сделки
            trade_size = float(trade.get("size", 0))

            # Рассчитать размер копии
            copy_size = self.calculate_copy_size(
                follower_balance,
                trade_size,
                trader_total_value,
                copy_pct,
            )

            if copy_size < 1.0:
                print(f"[CopyTrading] Copy size {copy_size} too small for user {follower_user_id}")
                return False

            # Исполнить сделку через CLOB API
            token_id = trade.get("token_id", "")
            side = trade.get("side", "BUY").upper()

            result = await clob.place_market_order(
                token_id=token_id,
                side=side,
                amount=copy_size,
                funder=follower_wallet,
            )

            if result and not result.get("error"):
                print(f"[CopyTrading] Copy trade executed for user {follower_user_id}")
                await self._notify_callbacks({
                    "type": "copy_executed",
                    "user_id": follower_user_id,
                    "trader": trader_address,
                    "size": copy_size,
                    "side": side,
                    "market_id": trade.get("market_id", ""),
                })
                return True
            else:
                error = result.get("error", "Unknown error") if result else "No response"
                print(f"[CopyTrading] Failed to execute copy for user {follower_user_id}: {error}")
                await self._notify_callbacks({
                    "type": "copy_failed",
                    "user_id": follower_user_id,
                    "trader": trader_address,
                    "error": error,
                })
                return False

        except Exception as e:
            print(f"[CopyTrading] Exception executing copy trade: {e}")
            await self._notify_callbacks({
                "type": "copy_failed",
                "user_id": follower_user_id,
                "trader": trader_address,
                "error": str(e),
            })
            return False

    # ─────────────────────────────────────────────────────────────────────
    # 5. Основной мониторинг — фоновый асинк-таск
    # ─────────────────────────────────────────────────────────────────────

    async def start_monitoring(self):
        """
        Запустить мониторинг сделок всех следимых трейдеров.
        Опрашивает API каждые 3 секунды.

        ВАЖНО: вызови это как фоновый asyncio.Task в главном боте:
            asyncio.create_task(copy_trading_service.start_monitoring())
        """
        self.monitoring = True
        print("[CopyTrading] Monitoring started")

        while self.monitoring:
            try:
                # Получить всех следимых трейдеров
                all_follows = await get_all_followed_traders()

                if not all_follows:
                    # Нет следимых трейдеров, ждём
                    await asyncio.sleep(3)
                    continue

                # Сгруппировать по трейдеру для уменьшения API-запросов
                traders = {}
                for follow in all_follows:
                    trader = follow["trader_address"]
                    if trader not in traders:
                        traders[trader] = []
                    traders[trader].append(follow)

                # Опросить каждого трейдера
                for trader_address, followers in traders.items():
                    try:
                        # Получить последние сделки трейдера
                        trades = await self.poll_trader(trader_address)

                        if not trades:
                            continue

                        # Для каждого последователя проверить новые сделки
                        for follower in followers:
                            user_id = follower["user_id"]
                            copy_pct = follower["copy_pct"]
                            last_trade_id = follower.get("last_trade_id", "")

                            # Найти новые сделки (после last_trade_id)
                            new_trades = []
                            for trade in trades:
                                trade_id = trade.get("id", "")
                                if trade_id and trade_id != last_trade_id:
                                    new_trades.append(trade)
                                else:
                                    break  # Остановиться на старых сделках

                            # Исполнить копии новых сделок
                            if new_trades:
                                # Получить кошелёк пользователя (нужна реализация в бизнес-логике)
                                # Для сейчас считаем, что wallet передаётся или получается из контекста
                                print(f"[CopyTrading] {len(new_trades)} new trades for trader {trader_address}")

                                for trade in new_trades:
                                    # ВАЖНО: здесь нужно получить follower_wallet из БД или контекста
                                    # Это заполнится через обработчик handlers/copy_trading.py
                                    trade_id = trade.get("id", "")
                                    if trade_id:
                                        await update_last_seen_trade(trader_address, trade_id)

                    except Exception as e:
                        print(f"[CopyTrading] Error processing trader {trader_address}: {e}")

                # Ждём перед следующим опросом
                await asyncio.sleep(3)

            except Exception as e:
                print(f"[CopyTrading] Monitoring error: {e}")
                await asyncio.sleep(3)

    def stop_monitoring(self):
        """Остановить мониторинг."""
        self.monitoring = False
        print("[CopyTrading] Monitoring stopped")


# Синглтон для использования в handlers
copy_trading_service = CopyTradingService()
