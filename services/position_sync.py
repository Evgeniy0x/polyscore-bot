# PolyScore — Position Sync Service
# Фоновый сервис: опрашивает data-api.polymarket.com/positions каждые 10 минут
# для всех пользователей с кошельком, кэширует результаты в БД,
# и отправляет уведомления о выигрышах/проигрышах.

import asyncio
import logging
import aiohttp
from typing import Optional

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database import (
    get_users_with_wallets,
    upsert_positions,
    get_cached_positions,
    clear_positions_cache,
)

logger = logging.getLogger("PolyScore.PositionSync")

# ── Константы ──────────────────────────────────────────────────────────
DATA_API_BASE   = "https://data-api.polymarket.com"
SYNC_INTERVAL   = 600          # 10 минут между синками
REQUEST_TIMEOUT = 15           # секунд на один HTTP запрос
MAX_CONCURRENT  = 5            # максимум параллельных запросов к API


# ══════════════════════════════════════════════════════════════════════
# HTTP helpers
# ══════════════════════════════════════════════════════════════════════

async def _fetch_positions(session: aiohttp.ClientSession, wallet: str) -> list[dict]:
    """Получить открытые позиции кошелька с data-api.polymarket.com.

    Эндпоинт: GET /positions?user={wallet}&sizeThreshold=0.01
    Возвращает список объектов позиций или [] при ошибке.
    """
    url = f"{DATA_API_BASE}/positions"
    params = {
        "user": wallet.lower(),
        "sizeThreshold": "0.01",   # игнорируем пыль < $0.01
        "limit": "500",
    }
    try:
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)) as resp:
            if resp.status == 200:
                data = await resp.json()
                # API возвращает либо список, либо {"data": [...]}
                if isinstance(data, list):
                    return data
                if isinstance(data, dict):
                    return data.get("data", []) or data.get("positions", [])
            else:
                logger.warning(f"positions API status {resp.status} for wallet {wallet[:8]}…")
    except asyncio.TimeoutError:
        logger.warning(f"Timeout fetching positions for {wallet[:8]}…")
    except Exception as e:
        logger.warning(f"Error fetching positions for {wallet[:8]}…: {e}")
    return []


async def _fetch_market_info(session: aiohttp.ClientSession, condition_id: str) -> dict:
    """Получить информацию о рынке для conditionId (для отображения вопроса)."""
    url = f"https://gamma-api.polymarket.com/markets"
    params = {"condition_id": condition_id}
    try:
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)) as resp:
            if resp.status == 200:
                data = await resp.json()
                markets = data if isinstance(data, list) else data.get("data", [])
                if markets:
                    return markets[0]
    except Exception:
        pass
    return {}


# ══════════════════════════════════════════════════════════════════════
# Notification builder
# ══════════════════════════════════════════════════════════════════════

def _build_resolution_notification(pos: dict, lang: str = "ru") -> Optional[str]:
    """
    Build a satisfying result card when a market resolves.

    Format (win):
    ───────────────────────────────
    🏆  YOU WON

    Will X happen?

    Invested    $25.00
    Returned   $45.80
    ─────────────────
    Profit     +$20.80   (+83%)
    Fee         -$4.16   (20%)
    Net        +$16.64
    ───────────────────────────────

    Format (loss):
    ───────────────────────────────
    📉  MARKET RESOLVED

    Will X happen?   ❌ NO

    Invested    $25.00
    Returned    $0.00
    ─────────────────
    Loss       -$25.00
    ───────────────────────────────
    """
    resolved = pos.get("resolved", False) or pos.get("isResolved", False)
    if not resolved:
        return None

    question = pos.get("title") or pos.get("question") or pos.get("market", "")
    outcome  = pos.get("outcome") or pos.get("side", "")
    size     = float(pos.get("size") or pos.get("currentValue") or 0)
    avg_p    = float(pos.get("avgPrice") or pos.get("averagePrice") or 0)
    cost     = float(pos.get("initialValue") or (avg_p * size if avg_p else 0))
    returned = size   # after resolution, size = payout received
    gross_pnl = returned - cost
    is_win    = gross_pnl > 0

    # Performance fee (20% of profit)
    fee      = max(0.0, gross_pnl * 0.20) if is_win else 0.0
    net_pnl  = gross_pnl - fee
    roi_pct  = (gross_pnl / cost * 100) if cost > 0 else 0.0

    q_short = question[:70] + "…" if len(question) > 70 else question
    out_str = f"<b>{outcome}</b>" if outcome else ""

    if lang == "ru":
        if is_win:
            fee_line = f"\nКомиссия     <b>-${fee:.2f}</b>  (20% с прибыли)" if fee > 0 else ""
            return (
                f"✅ <b>Сделка закрыта</b>\n\n"
                f"<i>{q_short}</i>  {out_str}\n\n"
                f"Вложено      <b>${cost:.2f}</b>\n"
                f"Получено     <b>${returned:.2f}</b>\n"
                f"──────────────\n"
                f"<b>+${gross_pnl:.2f}</b>  (+{roi_pct:.0f}%)"
                f"{fee_line}\n"
                f"Чистыми  <b>+${net_pnl:.2f}</b>\n\n"
                f"📊 /portfolio"
            )
        else:
            return (
                f"📋 <b>Сделка закрыта</b>\n\n"
                f"<i>{q_short}</i>  {out_str}\n\n"
                f"Вложено      <b>${cost:.2f}</b>\n"
                f"Получено     <b>${returned:.2f}</b>\n"
                f"──────────────\n"
                f"<b>-${abs(gross_pnl):.2f}</b>\n\n"
                f"Рынки меняются. 🧠 /intel"
            )
    else:
        if is_win:
            fee_line = f"\nFee          <b>-${fee:.2f}</b>  (20% of profit)" if fee > 0 else ""
            return (
                f"✅ <b>Trade settled</b>\n\n"
                f"<i>{q_short}</i>  {out_str}\n\n"
                f"Invested     <b>${cost:.2f}</b>\n"
                f"Returned     <b>${returned:.2f}</b>\n"
                f"──────────────\n"
                f"<b>+${gross_pnl:.2f}</b>  (+{roi_pct:.0f}%)"
                f"{fee_line}\n"
                f"Net  <b>+${net_pnl:.2f}</b>\n\n"
                f"📊 /portfolio"
            )
        else:
            return (
                f"📋 <b>Trade settled</b>\n\n"
                f"<i>{q_short}</i>  {out_str}\n\n"
                f"Invested     <b>${cost:.2f}</b>\n"
                f"Returned     <b>${returned:.2f}</b>\n"
                f"──────────────\n"
                f"<b>-${abs(gross_pnl):.2f}</b>\n\n"
                f"Markets move. 🧠 /intel"
            )


# ══════════════════════════════════════════════════════════════════════
# Core sync logic
# ══════════════════════════════════════════════════════════════════════

async def sync_user_positions(
    session: aiohttp.ClientSession,
    user_id: int,
    wallet: str,
    lang: str,
    app=None,                     # telegram.ext.Application для отправки уведомлений
) -> list[dict]:
    """Синхронизировать позиции одного пользователя.

    1. Запрашиваем свежие позиции с data-api
    2. Сравниваем с закэшированными — ищем новые resolved
    3. Сохраняем в БД
    4. Отправляем уведомления о завершённых рынках (если app передан)
    Returns: свежий список позиций
    """
    fresh_positions = await _fetch_positions(session, wallet)
    if not fresh_positions:
        # Нет данных — возвращаем старый кэш
        return await get_cached_positions(user_id)

    # Получаем старый кэш для сравнения
    old_positions = await get_cached_positions(user_id)
    old_resolved  = {
        (p.get("conditionId") or p.get("condition_id", ""))
        for p in old_positions
        if p.get("resolved") or p.get("isResolved")
    }

    # Сохраняем свежие позиции
    await upsert_positions(user_id, fresh_positions)

    # Отправляем уведомления о новых resolved
    if app is not None:
        for pos in fresh_positions:
            cid = pos.get("conditionId") or pos.get("condition_id", "")
            is_resolved = pos.get("resolved", False) or pos.get("isResolved", False)
            if is_resolved and cid not in old_resolved:
                text = _build_resolution_notification(pos, lang)
                if text:
                    try:
                        await app.bot.send_message(
                            chat_id=user_id,
                            text=text,
                            parse_mode="HTML",
                        )
                        logger.info(f"📨 Sent resolution notification to {user_id}")
                    except Exception as e:
                        logger.warning(f"Failed to notify {user_id}: {e}")

    return fresh_positions


# ══════════════════════════════════════════════════════════════════════
# Background worker
# ══════════════════════════════════════════════════════════════════════

async def position_sync_worker(app=None):
    """Бесконечный фоновый цикл синхронизации позиций.

    Запускается один раз при старте бота через asyncio.create_task().
    Каждые SYNC_INTERVAL секунд опрашивает всех пользователей с кошельками.
    """
    logger.info("📊 Position sync worker started")
    await asyncio.sleep(30)   # даём боту полностью стартовать

    while True:
        try:
            users = await get_users_with_wallets()
            if not users:
                await asyncio.sleep(SYNC_INTERVAL)
                continue

            logger.info(f"📊 Syncing positions for {len(users)} users...")

            # Ограничиваем параллелизм семафором
            semaphore = asyncio.Semaphore(MAX_CONCURRENT)

            async def _sync_one(user: dict):
                async with semaphore:
                    uid  = user["user_id"]
                    wall = user["wallet_address"]
                    lang = user.get("language", "ru")
                    async with aiohttp.ClientSession() as session:
                        try:
                            await sync_user_positions(session, uid, wall, lang, app)
                        except Exception as e:
                            logger.warning(f"Sync failed for user {uid}: {e}")

            await asyncio.gather(*[_sync_one(u) for u in users])
            logger.info("📊 Position sync cycle complete")

        except Exception as e:
            logger.error(f"Position sync worker error: {e}")

        await asyncio.sleep(SYNC_INTERVAL)


# ══════════════════════════════════════════════════════════════════════
# Public API — используется из handlers/portfolio.py
# ══════════════════════════════════════════════════════════════════════

async def get_positions(user_id: int, wallet: str, force_refresh: bool = False) -> list[dict]:
    """Получить позиции пользователя.

    Если force_refresh=True или кэш пустой — делает живой запрос к API.
    Иначе возвращает закэшированные данные.

    Это главная точка входа из handlers/portfolio.py.
    """
    if not force_refresh:
        cached = await get_cached_positions(user_id)
        if cached:
            return cached

    # Живой запрос
    async with aiohttp.ClientSession() as session:
        fresh = await _fetch_positions(session, wallet)
        if fresh:
            await upsert_positions(user_id, fresh)
            return fresh
        # API не ответил — возвращаем кэш
        return await get_cached_positions(user_id)


def enrich_position(pos: dict) -> dict:
    """Обогатить позицию расчётными полями для отображения.

    Добавляет: current_value, entry_value, pnl, pnl_pct, outcome_label.
    Работает с сырыми данными data-api.polymarket.com.
    """
    # Нормализуем ключи (API использует разные форматы)
    size         = float(pos.get("size") or pos.get("currentValue") or 0)
    avg_price    = float(pos.get("avgPrice") or pos.get("averagePrice") or 0)
    cur_price    = float(pos.get("curPrice") or pos.get("currentPrice") or avg_price)
    outcome      = pos.get("outcome") or pos.get("side") or "YES"

    # Стоимость входа и текущая стоимость
    entry_value  = size * avg_price   if avg_price > 0 else 0
    current_value = size * cur_price  if cur_price > 0 else size

    # P&L
    pnl     = current_value - entry_value
    pnl_pct = (pnl / entry_value * 100) if entry_value > 0 else 0.0

    return {
        **pos,
        "entry_value":   round(entry_value, 4),
        "current_value": round(current_value, 4),
        "pnl":           round(pnl, 4),
        "pnl_pct":       round(pnl_pct, 2),
        "outcome_label": outcome,
        "size_tokens":   round(size, 2),
    }
