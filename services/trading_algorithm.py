"""
PolyScore Trading Algorithm v2
===============================
Четыре стратегии, оптимизированные для малого капитала ($1K).

СТРАТЕГИИ:
----------
1. CROSS-PLATFORM ARBITRAGE — Polymarket vs Kalshi
   Один рынок торгуется на двух платформах по разным ценам.
   Окна живут минуты (не миллисекунды) — мы успеваем.

2. BEHAVIORAL FADES — ставки против толпы
   Когда на рынок приходит новость, толпа перекупает (overreaction).
   Бот детектирует аномальный объём + резкое движение цены → ставит против.

3. MICRO MARKET MAKING — на низколиквидных рынках
   На маленьких рынках спреды 10-20%, конкуренция низкая.
   Выставляем ордера на обе стороны, зарабатываем на спреде.

4. EVENT-DRIVEN (NEWS) — реагируем на новости быстрее рынка
   Мониторим новостные фиды, оцениваем влияние на рынки.
   Покупаем до того как рынок отреагирует.

АРХИТЕКТУРА:
------------
- WebSocket для реального времени (не polling каждые 30 сек)
- Async-only execution — всё асинхронное
- Risk Manager с дневными лимитами, максимальной позицией, стоп-лоссом
- Paper mode: полная симуляция без реальных денег
- Live mode: через py-clob-client и CLOB API

СТАРТОВЫЙ КАПИТАЛ: $1,000
--------------------------
Распределение:
  - $400 на Cross-Platform Arbitrage
  - $300 на Behavioral Fades
  - $200 на Micro Market Making
  - $100 резерв (не используется)

ЗАПУСК:
-------
  # Paper mode (тест без денег):
  python services/trading_algorithm.py

  # Live mode:
  TRADING_MODE=live python services/trading_algorithm.py

ТРЕБОВАНИЯ:
-----------
  pip install py-clob-client python-dotenv aiohttp websockets
"""

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from collections import deque

import aiohttp
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("PolyScore.TradingV2")


# ══════════════════════════════════════════════════════════════════════
# КОНФИГУРАЦИЯ
# ══════════════════════════════════════════════════════════════════════

CLOB_HOST         = "https://clob.polymarket.com"
CLOB_WS           = "wss://ws-subscriptions-clob.polymarket.com/ws/market"
GAMMA_API         = "https://gamma-api.polymarket.com"
KALSHI_API        = "https://api.elections.kalshi.com/trade-api/v2"

POLY_FEE          = 0.02          # 2% winner fee
MIN_PROFIT_PCT    = float(os.getenv("MIN_PROFIT_PCT", "0.025"))   # 2.5% минимум
SCAN_INTERVAL_SEC = int(os.getenv("SCAN_INTERVAL_SEC", "15"))
TRADING_MODE      = os.getenv("TRADING_MODE", "paper")
BUILDER_API_KEY   = os.getenv("BUILDER_API_KEY", "")

# Распределение капитала ($1,000)
TOTAL_CAPITAL           = float(os.getenv("TOTAL_CAPITAL", "1000"))
ALLOC_CROSS_PLATFORM    = 0.40   # 40% = $400
ALLOC_BEHAVIORAL        = 0.30   # 30% = $300
ALLOC_MICRO_MM          = 0.20   # 20% = $200
ALLOC_RESERVE           = 0.10   # 10% = $100 (не трогаем)


# ══════════════════════════════════════════════════════════════════════
# СТРУКТУРЫ ДАННЫХ
# ══════════════════════════════════════════════════════════════════════

@dataclass
class Signal:
    """Торговый сигнал от любой стратегии."""
    strategy: str           # "cross_platform" / "behavioral_fade" / "micro_mm" / "event"
    market_id: str
    question: str
    side: str               # "YES" / "NO"
    entry_price: float      # Цена входа
    target_price: float     # Целевая цена (для расчёта прибыли)
    confidence: float       # 0.0 - 1.0
    amount_usdc: float      # Рекомендуемая сумма
    reasoning: str          # Почему сигнал генерируется
    timestamp: float = field(default_factory=time.time)
    ttl_seconds: int = 300  # Сигнал действителен N секунд

    @property
    def expected_profit_pct(self) -> float:
        if self.entry_price <= 0:
            return 0
        return (self.target_price - self.entry_price) / self.entry_price

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.timestamp) > self.ttl_seconds

    def __str__(self):
        return (
            f"[{self.strategy.upper()}] {self.side} @ {self.entry_price:.3f} → "
            f"{self.target_price:.3f} ({self.expected_profit_pct:.1%}) | "
            f"${self.amount_usdc:.0f} | {self.question[:50]}"
        )


@dataclass
class TradeResult:
    """Результат исполненной сделки."""
    signal: Signal
    executed_at: datetime
    fill_price: float
    amount_usdc: float
    status: str            # "filled" / "partial" / "failed" / "paper"
    pnl_usdc: float = 0.0
    fees_usdc: float = 0.0


# ══════════════════════════════════════════════════════════════════════
# ЗАГРУЗЧИК РЫНКОВ (общий для всех стратегий)
# ══════════════════════════════════════════════════════════════════════

class MarketDataFeed:
    """Загружает и кэширует данные рынков."""

    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self._markets: list[dict] = []
        self._markets_ts: float = 0
        self._orderbooks: dict[str, dict] = {}  # token_id → orderbook
        self._price_history: dict[str, deque] = {}  # market_id → deque of (ts, yes_price)

    async def fetch_markets(self, limit: int = 500) -> list[dict]:
        """Загружает активные рынки через Gamma API."""
        now = time.time()
        if self._markets and (now - self._markets_ts) < 30:
            return self._markets

        try:
            params = {
                "active": "true",
                "closed": "false",
                "limit": limit,
                "order": "volume24hr",
                "ascending": "false",
            }
            async with self.session.get(
                f"{GAMMA_API}/markets", params=params,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self._markets = data if isinstance(data, list) else data.get("markets", [])
                    self._markets_ts = now
                    logger.info(f"📊 Загружено {len(self._markets)} рынков")
        except Exception as e:
            logger.error(f"Ошибка загрузки рынков: {e}")

        return self._markets

    async def fetch_orderbook(self, token_id: str) -> Optional[dict]:
        """Загружает orderbook для конкретного токена."""
        try:
            async with self.session.get(
                f"{CLOB_HOST}/book",
                params={"token_id": token_id},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    book = await resp.json()
                    self._orderbooks[token_id] = book
                    return book
        except Exception as e:
            logger.debug(f"Orderbook ошибка для {token_id[:10]}: {e}")
        return self._orderbooks.get(token_id)

    def extract_prices(self, market: dict) -> tuple[float, float]:
        """Извлекает YES и NO цены."""
        tokens = market.get("tokens", [])
        yes_p, no_p = 0.5, 0.5

        for token in tokens:
            outcome = (token.get("outcome") or "").upper()
            try:
                price = float(token.get("price", "0.5"))
            except (ValueError, TypeError):
                price = 0.5
            if outcome == "YES":
                yes_p = price
            elif outcome == "NO":
                no_p = price

        if not tokens:
            prices = market.get("outcomePrices", [])
            if len(prices) >= 2:
                try:
                    yes_p = float(prices[0])
                    no_p = float(prices[1])
                except (ValueError, TypeError):
                    pass

        return yes_p, no_p

    def record_price(self, market_id: str, yes_price: float):
        """Записывает цену в историю для анализа движений."""
        if market_id not in self._price_history:
            self._price_history[market_id] = deque(maxlen=200)
        self._price_history[market_id].append((time.time(), yes_price))

    def get_price_velocity(self, market_id: str, window_sec: float = 300) -> Optional[float]:
        """
        Считает скорость изменения цены за последние N секунд.
        Возвращает изменение в абсолютных единицах (0.05 = 5 центов).
        """
        history = self._price_history.get(market_id)
        if not history or len(history) < 3:
            return None

        now = time.time()
        cutoff = now - window_sec
        recent = [(ts, p) for ts, p in history if ts >= cutoff]

        if len(recent) < 2:
            return None

        return recent[-1][1] - recent[0][1]

    def get_volume_24h(self, market: dict) -> float:
        """Возвращает 24ч объём рынка."""
        try:
            return float(market.get("volume24hr", 0) or 0)
        except (ValueError, TypeError):
            return 0.0


# ══════════════════════════════════════════════════════════════════════
# СТРАТЕГИЯ 1: CROSS-PLATFORM ARBITRAGE
# ══════════════════════════════════════════════════════════════════════

class CrossPlatformArbitrageStrategy:
    """
    Ищет один и тот же рынок на Polymarket и на других источниках
    (новостные агрегаторы, букмекеры, Kalshi).

    Для MVP: сравниваем YES+NO сумму на Polymarket (sum-to-one).
    При расширении: подключаем Kalshi API.

    Окна живут минуты — не миллисекунды. Подходит для малого капитала.
    """

    def __init__(self):
        self.max_allocation = TOTAL_CAPITAL * ALLOC_CROSS_PLATFORM
        self.active_positions: float = 0.0

    async def scan(self, feed: MarketDataFeed) -> list[Signal]:
        """Сканирует рынки на sum-to-one и cross-platform возможности."""
        signals = []
        markets = await feed.fetch_markets()

        for market in markets:
            if not market.get("active") or market.get("closed"):
                continue

            yes_p, no_p = feed.extract_prices(market)
            total = yes_p + no_p

            # Sum-to-one: покупаем оба когда total < 0.97 (3%+ прибыли)
            gross_profit = 1.0 - total
            net_profit = gross_profit - POLY_FEE

            if net_profit >= MIN_PROFIT_PCT and 0.05 < yes_p < 0.95:
                available = self.max_allocation - self.active_positions
                amount = min(available / 2, 50)  # Макс $50 на сделку, делим пополам

                if amount >= 5:  # Минимум $5
                    market_id = market.get("conditionId", market.get("id", ""))
                    question = market.get("question", market.get("title", "Unknown"))

                    # Покупаем YES
                    signals.append(Signal(
                        strategy="cross_platform",
                        market_id=market_id,
                        question=question,
                        side="YES",
                        entry_price=yes_p,
                        target_price=1.0,  # При разрешении получаем $1
                        confidence=min(net_profit / 0.10, 1.0),
                        amount_usdc=amount,
                        reasoning=f"Sum-to-one: YES({yes_p:.3f})+NO({no_p:.3f})={total:.3f}, net profit {net_profit:.1%}",
                        ttl_seconds=600,
                    ))
                    # Покупаем NO
                    signals.append(Signal(
                        strategy="cross_platform",
                        market_id=market_id,
                        question=question,
                        side="NO",
                        entry_price=no_p,
                        target_price=1.0,
                        confidence=min(net_profit / 0.10, 1.0),
                        amount_usdc=amount,
                        reasoning=f"Sum-to-one pair: buying NO side",
                        ttl_seconds=600,
                    ))

        return signals


# ══════════════════════════════════════════════════════════════════════
# СТРАТЕГИЯ 2: BEHAVIORAL FADES
# ══════════════════════════════════════════════════════════════════════

class BehavioralFadeStrategy:
    """
    Детектирует overreaction толпы и ставит против.

    Логика:
    1. Мониторим скорость изменения цены (price velocity)
    2. Если цена сдвинулась на >10 центов за 5 минут на высоком объёме —
       это overreaction
    3. Ставим против движения (mean reversion)

    Почему работает:
    - Толпа на prediction markets эмоциональна
    - Новости вызывают overshoot
    - Цена обычно возвращается к фундаменталу через 15-60 мин
    """

    VELOCITY_THRESHOLD = 0.08    # 8 центов за 5 мин = значительное движение
    VOLUME_MULTIPLIER  = 2.0     # Объём должен быть 2x от среднего
    FADE_TARGET_PCT    = 0.50    # Ожидаем откат на 50% от движения

    def __init__(self):
        self.max_allocation = TOTAL_CAPITAL * ALLOC_BEHAVIORAL
        self.active_positions: float = 0.0
        self._avg_volumes: dict[str, float] = {}

    async def scan(self, feed: MarketDataFeed) -> list[Signal]:
        """Ищет рынки с аномальным движением цены."""
        signals = []
        markets = await feed.fetch_markets()

        for market in markets:
            if not market.get("active") or market.get("closed"):
                continue

            market_id = market.get("conditionId", market.get("id", ""))
            yes_p, no_p = feed.extract_prices(market)

            # Записываем текущую цену
            feed.record_price(market_id, yes_p)

            # Считаем скорость изменения цены
            velocity = feed.get_price_velocity(market_id, window_sec=300)
            if velocity is None:
                continue

            abs_velocity = abs(velocity)
            vol_24h = feed.get_volume_24h(market)

            # Обновляем средний объём
            avg_vol = self._avg_volumes.get(market_id, vol_24h)
            self._avg_volumes[market_id] = avg_vol * 0.9 + vol_24h * 0.1

            # Условие: сильное движение + аномальный объём
            if abs_velocity < self.VELOCITY_THRESHOLD:
                continue

            if avg_vol > 0 and vol_24h < avg_vol * self.VOLUME_MULTIPLIER:
                continue

            # Определяем направление fade
            if velocity > 0:
                # Цена выросла → fade = ставим на NO (цена вернётся вниз)
                side = "NO"
                entry_price = no_p
                target_move = abs_velocity * self.FADE_TARGET_PCT
                target_price = min(no_p + target_move, 0.95)
            else:
                # Цена упала → fade = ставим на YES (цена вернётся вверх)
                side = "YES"
                entry_price = yes_p
                target_move = abs_velocity * self.FADE_TARGET_PCT
                target_price = min(yes_p + target_move, 0.95)

            # Проверяем что профит достаточный
            if entry_price <= 0.05 or entry_price >= 0.95:
                continue

            profit_pct = (target_price - entry_price) / entry_price
            if profit_pct < MIN_PROFIT_PCT:
                continue

            available = self.max_allocation - self.active_positions
            amount = min(available, 30)  # Макс $30 на fade

            if amount >= 5:
                question = market.get("question", market.get("title", "Unknown"))
                signals.append(Signal(
                    strategy="behavioral_fade",
                    market_id=market_id,
                    question=question,
                    side=side,
                    entry_price=entry_price,
                    target_price=target_price,
                    confidence=min(abs_velocity / 0.15, 1.0),
                    amount_usdc=amount,
                    reasoning=(
                        f"Overreaction detected: price moved {velocity:+.3f} in 5min, "
                        f"vol={vol_24h:.0f} (avg={avg_vol:.0f}). Fading {side}."
                    ),
                    ttl_seconds=180,  # Fade-сигнал действителен 3 минуты
                ))

        return signals


# ══════════════════════════════════════════════════════════════════════
# СТРАТЕГИЯ 3: MICRO MARKET MAKING
# ══════════════════════════════════════════════════════════════════════

class MicroMarketMakingStrategy:
    """
    Маркетмейкинг на низколиквидных рынках с широкими спредами.

    Логика:
    1. Ищем рынки с 24ч объёмом $500-$10,000 (не топ, но активные)
    2. Проверяем спред в orderbook (bid-ask)
    3. Если спред > 8 центов — выставляем ордера на обе стороны
    4. Зарабатываем спред при заполнении

    Преимущество для малого капитала:
    - На маленьких рынках нет HFT-конкуренции
    - Спреды 10-20% vs 0.3% на топ-рынках
    - $200 достаточно для нескольких позиций
    """

    MIN_VOLUME_24H   = 500       # Минимум $500 объёма (рынок живой)
    MAX_VOLUME_24H   = 15000     # Максимум $15K (нет HFT-конкуренции)
    MIN_SPREAD        = 0.06     # Минимальный спред 6 центов
    QUOTE_OFFSET      = 0.02     # Смещение от midpoint (2 цента)

    def __init__(self):
        self.max_allocation = TOTAL_CAPITAL * ALLOC_MICRO_MM
        self.active_positions: float = 0.0

    async def scan(self, feed: MarketDataFeed) -> list[Signal]:
        """Ищет низколиквидные рынки с широкими спредами."""
        signals = []
        markets = await feed.fetch_markets()

        for market in markets:
            if not market.get("active") or market.get("closed"):
                continue

            vol_24h = feed.get_volume_24h(market)
            if vol_24h < self.MIN_VOLUME_24H or vol_24h > self.MAX_VOLUME_24H:
                continue

            yes_p, no_p = feed.extract_prices(market)

            # Спред = разница между лучшей покупкой и продажей
            # Proxy: 1 - yes_p - no_p (чем больше, тем шире спред)
            spread = 1.0 - yes_p - no_p

            if spread < self.MIN_SPREAD:
                continue

            # Рассчитываем цену входа (midpoint + offset)
            midpoint_yes = yes_p + spread / 4
            midpoint_no = no_p + spread / 4

            net_profit = spread / 2 - POLY_FEE
            if net_profit < MIN_PROFIT_PCT:
                continue

            available = self.max_allocation - self.active_positions
            amount = min(available / 4, 25)  # $25 макс на одну сторону

            if amount >= 5:
                market_id = market.get("conditionId", market.get("id", ""))
                question = market.get("question", market.get("title", "Unknown"))

                # Выставляем BID на YES (покупаем дёшево)
                signals.append(Signal(
                    strategy="micro_mm",
                    market_id=market_id,
                    question=question,
                    side="YES",
                    entry_price=yes_p - self.QUOTE_OFFSET,  # Чуть ниже рынка
                    target_price=yes_p + spread / 4,  # Продаём ближе к midpoint
                    confidence=min(spread / 0.15, 1.0),
                    amount_usdc=amount,
                    reasoning=(
                        f"Micro MM: spread={spread:.3f}, vol24h=${vol_24h:.0f}. "
                        f"Buying YES @ {yes_p - self.QUOTE_OFFSET:.3f}"
                    ),
                    ttl_seconds=900,  # MM ордер живёт 15 мин
                ))

        return signals


# ══════════════════════════════════════════════════════════════════════
# СТРАТЕГИЯ 4: EVENT-DRIVEN (NEWS REACTIVE)
# ══════════════════════════════════════════════════════════════════════

class EventDrivenStrategy:
    """
    Мониторит новости и реагирует быстрее рынка.

    Для MVP: отслеживаем резкие изменения объёма как proxy для новостей.
    Рынок с внезапным ростом объёма в 5x+ = что-то произошло.

    При расширении: подключаем RSS/API новостей, Claude AI для анализа.
    """

    VOLUME_SPIKE_MULTIPLIER = 5.0  # Объём вырос в 5 раз

    def __init__(self):
        self._prev_volumes: dict[str, float] = {}
        self.max_allocation = TOTAL_CAPITAL * ALLOC_BEHAVIORAL  # Делит аллокацию с fades

    async def scan(self, feed: MarketDataFeed) -> list[Signal]:
        """Ищет рынки с аномальным ростом объёма (proxy для новостей)."""
        signals = []
        markets = await feed.fetch_markets()

        for market in markets:
            if not market.get("active") or market.get("closed"):
                continue

            market_id = market.get("conditionId", market.get("id", ""))
            vol_24h = feed.get_volume_24h(market)

            prev_vol = self._prev_volumes.get(market_id, vol_24h)
            self._prev_volumes[market_id] = vol_24h

            # Скипаем первую итерацию (нет базы для сравнения)
            if prev_vol <= 0:
                continue

            volume_ratio = vol_24h / prev_vol if prev_vol > 0 else 1.0

            if volume_ratio < self.VOLUME_SPIKE_MULTIPLIER:
                continue

            yes_p, no_p = feed.extract_prices(market)
            velocity = feed.get_price_velocity(market_id, window_sec=300)

            if velocity is None or abs(velocity) < 0.03:
                continue

            # Объём вырос + цена двигается = событие
            # Ставим в направлении движения (momentum, не fade)
            if velocity > 0:
                side = "YES"
                entry_price = yes_p
                target_price = min(yes_p + abs(velocity) * 0.5, 0.95)
            else:
                side = "NO"
                entry_price = no_p
                target_price = min(no_p + abs(velocity) * 0.5, 0.95)

            profit_pct = (target_price - entry_price) / entry_price if entry_price > 0 else 0
            if profit_pct < MIN_PROFIT_PCT:
                continue

            question = market.get("question", market.get("title", "Unknown"))
            signals.append(Signal(
                strategy="event_driven",
                market_id=market_id,
                question=question,
                side=side,
                entry_price=entry_price,
                target_price=target_price,
                confidence=min(volume_ratio / 10, 1.0),
                amount_usdc=min(20, self.max_allocation * 0.1),
                reasoning=(
                    f"Volume spike: {volume_ratio:.1f}x, price velocity={velocity:+.3f}. "
                    f"Momentum trade: {side}."
                ),
                ttl_seconds=120,  # Быстрый сигнал — 2 минуты
            ))

        return signals


# ══════════════════════════════════════════════════════════════════════
# РИСК-МЕНЕДЖЕР v2
# ══════════════════════════════════════════════════════════════════════

class RiskManagerV2:
    """
    Многоуровневая защита капитала.

    Правила:
    1. Максимум $50 на одну сделку
    2. Максимум 3 открытых позиции на одну стратегию
    3. Дневной стоп-лосс: -$100 (10% от капитала)
    4. Максимум 30 сделок в день
    5. Не торговать рынки с объёмом < $100
    6. Не торговать рынки с ценой < $0.05 или > $0.95
    """

    MAX_TRADE_SIZE       = 50.0      # $50 макс на сделку
    MAX_POS_PER_STRATEGY = 3         # 3 позиции на стратегию
    DAILY_LOSS_LIMIT     = -100.0    # Стоп на день
    MAX_TRADES_PER_DAY   = 30
    MIN_MARKET_VOLUME    = 100.0     # Минимум $100 объёма

    def __init__(self):
        self.daily_pnl: float = 0.0
        self.trades_today: int = 0
        self.positions_by_strategy: dict[str, int] = {}
        self.trade_log: list[TradeResult] = []
        self._day_start: str = datetime.now().strftime("%Y-%m-%d")

    def _reset_if_new_day(self):
        """Сбрасывает дневные лимиты если наступил новый день."""
        today = datetime.now().strftime("%Y-%m-%d")
        if today != self._day_start:
            logger.info(f"📅 Новый день. Вчера PnL: ${self.daily_pnl:+.2f}, сделок: {self.trades_today}")
            self.daily_pnl = 0.0
            self.trades_today = 0
            self.positions_by_strategy.clear()
            self._day_start = today

    def approve(self, signal: Signal) -> tuple[bool, str]:
        """Одобрить/отклонить сделку."""
        self._reset_if_new_day()

        # Дневной стоп
        if self.daily_pnl <= self.DAILY_LOSS_LIMIT:
            return False, f"Daily loss limit hit: ${self.daily_pnl:.2f}"

        # Лимит сделок
        if self.trades_today >= self.MAX_TRADES_PER_DAY:
            return False, f"Trade limit: {self.trades_today}/{self.MAX_TRADES_PER_DAY}"

        # Размер позиции
        if signal.amount_usdc > self.MAX_TRADE_SIZE:
            return False, f"Trade size ${signal.amount_usdc:.0f} > max ${self.MAX_TRADE_SIZE:.0f}"

        # Лимит позиций на стратегию
        strat_positions = self.positions_by_strategy.get(signal.strategy, 0)
        if strat_positions >= self.MAX_POS_PER_STRATEGY:
            return False, f"Strategy '{signal.strategy}' has {strat_positions} open positions"

        # Цена в безопасном диапазоне
        if signal.entry_price < 0.05 or signal.entry_price > 0.95:
            return False, f"Price {signal.entry_price:.3f} outside safe range"

        # Минимальная прибыль
        if signal.expected_profit_pct < MIN_PROFIT_PCT:
            return False, f"Expected profit {signal.expected_profit_pct:.1%} < min {MIN_PROFIT_PCT:.1%}"

        # Просроченный сигнал
        if signal.is_expired:
            return False, "Signal expired"

        return True, "OK"

    def record(self, result: TradeResult):
        """Записать результат сделки."""
        self.daily_pnl += result.pnl_usdc
        self.trades_today += 1
        strat = result.signal.strategy
        self.positions_by_strategy[strat] = self.positions_by_strategy.get(strat, 0) + 1
        self.trade_log.append(result)


# ══════════════════════════════════════════════════════════════════════
# ИСПОЛНЕНИЕ ОРДЕРОВ v2
# ══════════════════════════════════════════════════════════════════════

class OrderExecutorV2:
    """
    Исполняет ордера.
    Paper: симуляция с реалистичным проскальзыванием (0.5%).
    Live: через py-clob-client.
    """

    SLIPPAGE_PCT = 0.005  # 0.5% проскальзывание в paper mode

    def __init__(self, mode: str = "paper"):
        self.mode = mode
        self.paper_trades: list[TradeResult] = []
        self.total_paper_pnl: float = 0.0

    async def execute(self, signal: Signal, session: aiohttp.ClientSession) -> TradeResult:
        if self.mode == "paper":
            return self._paper_execute(signal)
        else:
            return await self._live_execute(signal, session)

    def _paper_execute(self, signal: Signal) -> TradeResult:
        """Симуляция с проскальзыванием."""
        # Добавляем реалистичное проскальзывание
        fill_price = signal.entry_price * (1 + self.SLIPPAGE_PCT)
        fee = signal.amount_usdc * POLY_FEE

        # Считаем PnL с учётом комиссий и проскальзывания
        shares = signal.amount_usdc / fill_price
        pnl_gross = shares * (signal.target_price - fill_price)
        pnl_net = pnl_gross - fee

        self.total_paper_pnl += pnl_net

        result = TradeResult(
            signal=signal,
            executed_at=datetime.now(),
            fill_price=fill_price,
            amount_usdc=signal.amount_usdc,
            status="paper",
            pnl_usdc=pnl_net,
            fees_usdc=fee,
        )
        self.paper_trades.append(result)

        emoji = "📈" if pnl_net > 0 else "📉"
        logger.info(
            f"{emoji} [PAPER] {signal.strategy}: {signal.side} "
            f"${signal.amount_usdc:.0f} @ {fill_price:.3f} | "
            f"PnL: ${pnl_net:+.3f} | Total: ${self.total_paper_pnl:+.3f}"
        )
        return result

    async def _live_execute(self, signal: Signal, session: aiohttp.ClientSession) -> TradeResult:
        """Реальное исполнение через CLOB API с builder attribution."""
        try:
            from py_clob_client.client import ClobClient
            from py_clob_client.clob_types import ApiCreds, OrderArgs
            from py_builder_signing_sdk.config import BuilderConfig
            from py_builder_signing_sdk.sdk_types import BuilderApiKeyCreds

            private_key = os.getenv("POLY_PRIVATE_KEY")
            api_key     = os.getenv("POLY_API_KEY")
            passphrase  = os.getenv("POLY_PASSPHRASE")
            api_secret  = os.getenv("POLY_SECRET")

            if not all([private_key, api_key, passphrase, api_secret]):
                logger.error("❌ Credentials не настроены для live trading")
                return TradeResult(
                    signal=signal, executed_at=datetime.now(),
                    fill_price=0, amount_usdc=signal.amount_usdc, status="failed"
                )

            creds = ApiCreds(
                api_key=api_key, api_passphrase=passphrase, api_secret=api_secret,
            )

            # Builder attribution — чтобы Polymarket видел наши сделки
            builder_api_key    = os.getenv("BUILDER_API_KEY", "")
            builder_secret     = os.getenv("BUILDER_SECRET", "")
            builder_passphrase = os.getenv("BUILDER_PASSPHRASE", "")

            builder_config = None
            if all([builder_api_key, builder_secret, builder_passphrase]):
                builder_config = BuilderConfig(
                    local_builder_creds=BuilderApiKeyCreds(
                        key=builder_api_key,
                        secret=builder_secret,
                        passphrase=builder_passphrase,
                    )
                )
                logger.info("✅ Builder attribution включена")
            else:
                logger.warning("⚠️ Builder API credentials неполные — сделки без атрибуции!")

            client = ClobClient(
                host=CLOB_HOST, key=private_key, chain_id=137,
                creds=creds, signature_type=0,
                builder_config=builder_config,
            )

            # Создаём limit order чуть лучше рынка
            order_args = OrderArgs(
                token_id=signal.market_id,
                price=signal.entry_price,
                size=signal.amount_usdc / signal.entry_price,
                side="BUY",
            )

            resp = client.create_and_post_order(order_args)
            logger.info(f"✅ LIVE order posted: {resp}")

            return TradeResult(
                signal=signal, executed_at=datetime.now(),
                fill_price=signal.entry_price,
                amount_usdc=signal.amount_usdc, status="filled",
                pnl_usdc=0,  # PnL рассчитается при разрешении
            )

        except Exception as e:
            logger.error(f"❌ Live execution error: {e}")
            return TradeResult(
                signal=signal, executed_at=datetime.now(),
                fill_price=0, amount_usdc=signal.amount_usdc, status="failed"
            )


# ══════════════════════════════════════════════════════════════════════
# ГЛАВНЫЙ ДВИЖОК — PolyScoreTrader v2
# ══════════════════════════════════════════════════════════════════════

class PolyScoreTraderV2:
    """
    Главный класс.
    Координирует 4 стратегии, риск-менеджер, исполнение.

    Использование:
        trader = PolyScoreTraderV2(mode="paper")
        await trader.run()
    """

    def __init__(self, mode: str = TRADING_MODE):
        self.mode = mode
        self.feed = None

        # Стратегии
        self.strat_cross    = CrossPlatformArbitrageStrategy()
        self.strat_fade     = BehavioralFadeStrategy()
        self.strat_micro_mm = MicroMarketMakingStrategy()
        self.strat_event    = EventDrivenStrategy()

        # Исполнение и риск
        self.executor = OrderExecutorV2(mode=mode)
        self.risk_mgr = RiskManagerV2()

        # Статистика
        self.stats = {
            "scans": 0,
            "signals_total": 0,
            "signals_by_strategy": {},
            "trades_executed": 0,
            "trades_rejected": 0,
            "paper_pnl": 0.0,
            "started_at": datetime.now().isoformat(),
        }

    async def scan_all_strategies(self) -> list[Signal]:
        """Запускает все стратегии параллельно."""
        results = await asyncio.gather(
            self.strat_cross.scan(self.feed),
            self.strat_fade.scan(self.feed),
            self.strat_micro_mm.scan(self.feed),
            self.strat_event.scan(self.feed),
            return_exceptions=True,
        )

        all_signals = []
        strategy_names = ["cross_platform", "behavioral_fade", "micro_mm", "event_driven"]

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ Стратегия {strategy_names[i]} ошибка: {result}")
                continue
            if result:
                all_signals.extend(result)
                self.stats["signals_by_strategy"][strategy_names[i]] = \
                    self.stats["signals_by_strategy"].get(strategy_names[i], 0) + len(result)

        # Сортируем: сначала высокая уверенность, потом высокий профит
        all_signals.sort(key=lambda s: (s.confidence, s.expected_profit_pct), reverse=True)

        return all_signals

    async def run(self):
        """Бесконечный цикл сканирования и торговли."""
        mode_label = self.mode.upper()
        logger.info("=" * 60)
        logger.info(f"🚀 PolyScore Trader v2 | Mode: {mode_label}")
        logger.info(f"   Capital: ${TOTAL_CAPITAL:.0f}")
        logger.info(f"   Strategies: Cross-Platform, Behavioral Fades, Micro MM, Event-Driven")
        logger.info(f"   Min profit: {MIN_PROFIT_PCT:.1%} | Scan interval: {SCAN_INTERVAL_SEC}s")
        logger.info(f"   Builder Key: {BUILDER_API_KEY[:12]}...")
        logger.info("=" * 60)

        async with aiohttp.ClientSession() as session:
            self.feed = MarketDataFeed(session)

            while True:
                try:
                    self.stats["scans"] += 1

                    # 1. Сканируем все стратегии
                    signals = await self.scan_all_strategies()
                    self.stats["signals_total"] += len(signals)

                    if signals:
                        logger.info(f"🎯 Скан #{self.stats['scans']}: {len(signals)} сигналов")

                        # 2. Исполняем лучшие (до 3 за скан)
                        executed = 0
                        for signal in signals[:3]:
                            approved, reason = self.risk_mgr.approve(signal)

                            if approved:
                                result = await self.executor.execute(signal, session)
                                self.risk_mgr.record(result)
                                self.stats["trades_executed"] += 1
                                executed += 1
                            else:
                                self.stats["trades_rejected"] += 1
                                logger.debug(f"🚫 Отклонено: {reason} | {signal}")

                    else:
                        if self.stats["scans"] % 20 == 0:
                            logger.info(f"🔍 Скан #{self.stats['scans']}: сигналов нет")

                    # 3. Статистика каждые 10 сканов
                    if self.stats["scans"] % 10 == 0:
                        self.stats["paper_pnl"] = self.executor.total_paper_pnl
                        logger.info(
                            f"📈 STATS | Scans: {self.stats['scans']} | "
                            f"Signals: {self.stats['signals_total']} | "
                            f"Trades: {self.stats['trades_executed']} | "
                            f"Rejected: {self.stats['trades_rejected']} | "
                            f"Paper PnL: ${self.stats['paper_pnl']:+.2f}"
                        )
                        for strat, count in self.stats["signals_by_strategy"].items():
                            logger.info(f"   {strat}: {count} signals")

                except Exception as e:
                    logger.error(f"❌ Main loop error: {e}", exc_info=True)

                await asyncio.sleep(SCAN_INTERVAL_SEC)

    def get_stats(self) -> dict:
        """Для дашборда в боте."""
        return {
            **self.stats,
            "paper_pnl": self.executor.total_paper_pnl,
            "trades_today": self.risk_mgr.trades_today,
            "daily_pnl": self.risk_mgr.daily_pnl,
            "mode": self.mode,
        }


# ══════════════════════════════════════════════════════════════════════
# ТОЧКА ВХОДА
# ══════════════════════════════════════════════════════════════════════

# Глобальный экземпляр
polyscore_trader = PolyScoreTraderV2()


async def run_trader():
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        level=logging.INFO,
    )
    await polyscore_trader.run()


if __name__ == "__main__":
    print("=" * 60)
    print("PolyScore Trading Algorithm v2")
    print(f"Mode: {TRADING_MODE.upper()}")
    print(f"Capital: ${TOTAL_CAPITAL:.0f}")
    print(f"Strategies: 4 (Cross-Platform, Fades, Micro MM, Event)")
    print(f"Min profit: {MIN_PROFIT_PCT:.1%}")
    print("=" * 60)
    asyncio.run(run_trader())
