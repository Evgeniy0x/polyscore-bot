# PolyScore — 🧠 Intel Mode  (UX v2 — Feed-first redesign)
# ────────────────────────────────────────────────────────
# Design principle: feel like a live trading terminal, not a menu.
# Every screen shows ONE thing + ONE clear action.
#
# Feed format:
#   [Whale block]   — most recent large trade
#   [Signal block]  — top-priority signal  (SignalCard)
#   [Queue line]    — "N more signals ↓"
#
# Buttons (max 4):
#   Row 1: [⚡ Trade $25]  [⚡ Trade $50]
#   Row 2: [📊 View]       [❌ Skip]
#   (no wallet):
#   Row 1: [🔓 Connect wallet to trade]
#   Row 2: [⏭ Next]       [🔙 Menu]
#
# Entry: /intel  |  callback intel:feed  |  callback intel:refresh
# No wallet required to VIEW.  Wallet required to TRADE.

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database import get_user
from services.polymarket import gamma
from services.signal_pipeline import signal_pipeline, SignalCard


# ══════════════════════════════════════════════════════════════════════
# i18n strings — ONLY what's actually shown (kept minimal)
# ══════════════════════════════════════════════════════════════════════

def _t(ru: str, en: str, lang: str) -> str:
    return ru if lang == "ru" else en


_LOADING = {
    "ru": "⚡ <i>Ищу лучшие возможности…</i>",
    "en": "⚡ <i>Scanning for best opportunities…</i>",
    "es": "⚡ <i>Buscando las mejores oportunidades…</i>",
    "pt": "⚡ <i>Buscando as melhores oportunidades…</i>",
    "tr": "⚡ <i>En iyi fırsatlar aranıyor…</i>",
    "id": "⚡ <i>Mencari peluang terbaik…</i>",
    "zh": "⚡ <i>正在扫描最佳机会…</i>",
    "ar": "⚡ <i>البحث عن أفضل الفرص…</i>",
    "fr": "⚡ <i>Recherche des meilleures opportunités…</i>",
    "de": "⚡ <i>Suche nach den besten Möglichkeiten…</i>",
    "hi": "⚡ <i>सर्वोत्तम अवसरों की खोज…</i>",
    "ja": "⚡ <i>最良の機会を探しています…</i>",
}

_EMPTY_FEED = {
    "ru": (
        "🧠 <b>Intel Feed</b>\n\n"
        "Сигналов нет прямо сейчас.\n"
        "Рынки спокойные — попробуй через 15 мин."
    ),
    "en": (
        "🧠 <b>Intel Feed</b>\n\n"
        "No signals right now.\n"
        "Markets are quiet — try again in 15 min."
    ),
}


# ══════════════════════════════════════════════════════════════════════
# Signal Card Storage in bot_data
# key: "sc"  value: {int → SignalCard}
# separate from market cache "mc"
# ══════════════════════════════════════════════════════════════════════

def _store_signal(ctx: ContextTypes.DEFAULT_TYPE, signal: SignalCard) -> int:
    if "sc" not in ctx.bot_data:
        ctx.bot_data["sc"] = {}
        ctx.bot_data["sc_next"] = 0
    idx = ctx.bot_data["sc_next"]
    ctx.bot_data["sc"][idx] = signal
    ctx.bot_data["sc_next"] = idx + 1
    # Cap at 50, evict oldest 25
    if len(ctx.bot_data["sc"]) > 50:
        for k in sorted(ctx.bot_data["sc"].keys())[:25]:
            del ctx.bot_data["sc"][k]
    return idx


def get_signal(ctx: ContextTypes.DEFAULT_TYPE, idx: int) -> SignalCard | None:
    return ctx.bot_data.get("sc", {}).get(idx)


# ══════════════════════════════════════════════════════════════════════
# Feed builder — one function, one format, used everywhere
# ══════════════════════════════════════════════════════════════════════

def _build_signal_card_text(signal: SignalCard, lang: str) -> str:
    """
    THE standard Signal Card text format.
    Used in Intel Feed, AI briefing, notifications.
    Short. Scannable. Actionable.

    Format:
    ┌──────────────────────────────────────┐
    │ 🔴 HIGH  ·  🤖 AI Model             │
    │                                      │
    │ Will Trump win in 2025?              │
    │                                      │
    │ Direction  YES         Price   62¢   │
    │ Fair value 74¢         Edge   +12%   │
    │                                      │
    │ 💡 Polls show 74%, market lags       │
    │ ⚠️  Resolves in 3 days, illiquid     │
    └──────────────────────────────────────┘
    """
    priority_label = {
        "HIGH":   {"ru": "СРОЧНО",    "en": "ACT NOW"},
        "MEDIUM": {"ru": "СЛЕДИ",     "en": "WATCH"},
        "LOW":    {"ru": "ФОНОВЫЙ",   "en": "OPTIONAL"},
    }.get(signal.priority, {"ru": "СИГНАЛ", "en": "SIGNAL"})

    p_lbl = priority_label.get(lang, priority_label["en"])
    prio_emoji = signal.priority_emoji          # 🔴 / 🟡 / ⚪

    # Price display
    price_cents = f"{signal.current_price * 100:.0f}¢"
    model_cents = f"{signal.fair_value * 100:.0f}¢"
    edge_str    = signal.edge_display           # e.g. "+12.4%"

    # Closing date (compact, inline)
    closes_line = ""
    if signal.market_closes:
        closes_line = f"  ·  ⏰ {signal.market_closes}"

    if lang == "ru":
        return (
            f"{prio_emoji} <b>{p_lbl}</b>  ·  {signal.source_label}\n"
            f"\n"
            f"<b>{signal.question}</b>\n"
            f"\n"
            f"<b>{signal.direction}</b>   {price_cents}  →  model {model_cents}   <b>{edge_str}</b>\n"
            f"\n"
            f"💡 {signal.reason}\n"
            f"⚠️ {signal.risk}{closes_line}"
        )
    else:
        return (
            f"{prio_emoji} <b>{p_lbl}</b>  ·  {signal.source_label}\n"
            f"\n"
            f"<b>{signal.question}</b>\n"
            f"\n"
            f"<b>{signal.direction}</b>   {price_cents}  →  model {model_cents}   <b>{edge_str}</b>\n"
            f"\n"
            f"💡 {signal.reason}\n"
            f"⚠️ {signal.risk}{closes_line}"
        )


def _build_signal_keyboard(
    sc_idx: int,
    signal: SignalCard,
    lang: str,
    has_wallet: bool,
    show_skip: bool = True,
    extra_context: str = "intel",   # "intel" | "feed"
) -> InlineKeyboardMarkup:
    """
    THE standard Signal Card keyboard.
    Used in Intel Feed and anywhere a SignalCard is shown.

    With wallet:
      Row 1: [⚡ Trade $25]  [⚡ Trade $50]
      Row 2: [📊 View]       [❌ Skip]

    Without wallet:
      Row 1: [🔓 Connect wallet to trade]
      Row 2: [⏭ Next]       [🔙 Menu]
    """
    buttons = []

    if has_wallet:
        # Dual-amount trade buttons
        a1 = 25
        a2 = 50
        dir_code = "Y" if signal.direction == "YES" else "N"
        buttons.append([
            InlineKeyboardButton(
                f"⚡ {_t('Купить', 'Trade', lang)} ${a1}",
                callback_data=f"intel:trade:{sc_idx}:{a1}"
            ),
            InlineKeyboardButton(
                f"⚡ {_t('Купить', 'Trade', lang)} ${a2}",
                callback_data=f"intel:trade:{sc_idx}:{a2}"
            ),
        ])
        view_label  = _t("📊 Рынок", "📊 View", lang)
        skip_label  = _t("❌ Пропустить", "❌ Skip", lang)
        buttons.append([
            InlineKeyboardButton(view_label, callback_data=f"intel:view:{sc_idx}"),
            InlineKeyboardButton(skip_label, callback_data=f"intel:skip:{sc_idx}"),
        ])
    else:
        connect_label = _t("🔓 Подключи кошелёк → торгуй", "🔓 Connect wallet → trade", lang)
        buttons.append([
            InlineKeyboardButton(connect_label, callback_data=f"intel:wallet_prompt:{sc_idx}"),
        ])
        next_label = _t("⏭ Следующий", "⏭ Next", lang)
        menu_label = _t("🔙 Меню", "🔙 Menu", lang)
        buttons.append([
            InlineKeyboardButton(next_label, callback_data=f"intel:skip:{sc_idx}"),
            InlineKeyboardButton(menu_label, callback_data="menu:main"),
        ])

    return InlineKeyboardMarkup(buttons)


def _build_feed_text(signals: list[SignalCard], lang: str, ctx: ContextTypes.DEFAULT_TYPE) -> tuple[str, int]:
    """
    Build the primary feed text.
    Returns (text, primary_sc_idx).
    Shows: primary SignalCard + compact list of remaining.
    """
    primary = signals[0]
    primary_idx = _store_signal(ctx, primary)

    # Header line — show queue depth
    remaining = len(signals) - 1
    if remaining > 0:
        queue_line = _t(
            f"<i>Ещё {remaining} сигнал{'а' if remaining < 5 else 'ов'} в очереди  →</i>",
            f"<i>{remaining} more signal{'s' if remaining != 1 else ''} in queue  →</i>",
            lang
        )
    else:
        queue_line = _t("<i>Это единственный сигнал сейчас</i>", "<i>Only signal right now</i>", lang)

    card_text = _build_signal_card_text(primary, lang)

    text = f"🧠 <b>Intel Feed</b>  {queue_line}\n\n{card_text}"
    return text, primary_idx


# ══════════════════════════════════════════════════════════════════════
# Whale block — compact top-of-feed whale trade display
# ══════════════════════════════════════════════════════════════════════

async def _get_whale_block(lang: str) -> str:
    """
    Fetch 1 recent large trade and format it as a compact 2-line block.
    Returns "" on failure.
    """
    try:
        import aiohttp
        url = "https://data-api.polymarket.com/trades"
        params = {"limit": "20", "taker_only": "true"}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status != 200:
                    return ""
                data = await resp.json()
                trades = data if isinstance(data, list) else data.get("data", [])

                # Find largest trade
                whale = None
                for t in trades:
                    size = float(t.get("usdcSize") or t.get("size") or 0)
                    if size >= 1000:
                        whale = t
                        break

                if not whale:
                    return ""

                size  = float(whale.get("usdcSize") or whale.get("size") or 0)
                side  = whale.get("side") or whale.get("outcome", "")
                title = whale.get("title") or whale.get("market", "")
                if len(title) > 48:
                    title = title[:45] + "…"
                price = float(whale.get("price") or 0)
                price_s = f"{price * 100:.0f}¢" if price else ""

                # Try to get trade timing
                trade_ts = whale.get("timestamp") or whale.get("createdAt") or ""
                time_str = ""
                if trade_ts:
                    try:
                        import datetime
                        ts = int(str(trade_ts)[:10])
                        delta = int(datetime.datetime.utcnow().timestamp()) - ts
                        if delta < 3600:
                            mins = delta // 60
                            time_str = f"  {mins}m ago" if lang != "ru" else f"  {mins} мин назад"
                        elif delta < 86400:
                            hrs = delta // 3600
                            time_str = f"  {hrs}h ago" if lang != "ru" else f"  {hrs} ч назад"
                    except Exception:
                        pass

                if lang == "ru":
                    return (
                        f"🐋 ${size:,.0f}  {side} {price_s}  —  {title}{time_str}"
                    )
                else:
                    return (
                        f"🐋 ${size:,.0f}  {side} {price_s}  —  {title}{time_str}"
                    )
    except Exception:
        return ""


# ══════════════════════════════════════════════════════════════════════
# Handlers
# ══════════════════════════════════════════════════════════════════════

async def _show_feed(query, ctx: ContextTypes.DEFAULT_TYPE, force_refresh: bool = False):
    """
    Core feed renderer — shared by cb_intel_feed and cb_intel_refresh.
    """
    user = await get_user(query.from_user.id)
    lang = (user or {}).get("language", "en")
    has_wallet = bool((user or {}).get("wallet_address"))

    await query.edit_message_text(
        _LOADING.get(lang, _LOADING["en"]), parse_mode="HTML"
    )

    if force_refresh:
        signal_pipeline.clear_cache()

    # Fetch signals and whale block concurrently
    import asyncio
    markets = await gamma.get_trending_markets(limit=12)
    if not markets:
        markets = await gamma.get_sports_markets(limit=12, tag="sports")

    signals, whale_text = await asyncio.gather(
        signal_pipeline.get_feed(markets, max_signals=8),
        _get_whale_block(lang),
    )

    if not signals:
        empty = _EMPTY_FEED.get(lang, _EMPTY_FEED["en"])
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                _t("🔄 Попробовать снова", "🔄 Try again", lang),
                callback_data="intel:refresh"
            )],
            [InlineKeyboardButton(
                _t("🔙 Меню", "🔙 Menu", lang),
                callback_data="menu:main"
            )],
        ])
        await query.edit_message_text(empty, parse_mode="HTML", reply_markup=keyboard)
        return

    feed_text, primary_idx = _build_feed_text(signals, lang, ctx)

    # Prepend whale block if available
    if whale_text:
        full_text = f"{whale_text}\n\n━━━━\n\n{feed_text}"
    else:
        full_text = feed_text

    keyboard = _build_signal_keyboard(primary_idx, signals[0], lang, has_wallet)

    await query.edit_message_text(full_text, parse_mode="HTML", reply_markup=keyboard)


async def cb_intel_feed(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Callback: intel:feed"""
    query = update.callback_query
    await query.answer()
    await _show_feed(query, ctx, force_refresh=False)


async def cb_intel_refresh(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Callback: intel:refresh — force clear cache and reload."""
    query = update.callback_query
    await query.answer()
    await _show_feed(query, ctx, force_refresh=True)


async def cb_intel_skip(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    Callback: intel:skip:{sc_idx}
    Rotate to the next signal in cache without reloading from API.
    """
    query = update.callback_query
    await query.answer()

    user = await get_user(query.from_user.id)
    lang = (user or {}).get("language", "en")
    has_wallet = bool((user or {}).get("wallet_address"))

    parts = query.data.split(":")
    try:
        current_idx = int(parts[2])
    except (IndexError, ValueError):
        current_idx = -1

    # Collect all cached signals after current idx
    sc_store = ctx.bot_data.get("sc", {})
    future_signals = [
        sc_store[k] for k in sorted(sc_store.keys())
        if k > current_idx and not sc_store[k].is_expired
    ]

    if future_signals:
        next_signal = future_signals[0]
        next_idx = _store_signal(ctx, next_signal)
        text = f"🧠 <b>Intel Feed</b>\n\n{_build_signal_card_text(next_signal, lang)}"
        keyboard = _build_signal_keyboard(next_idx, next_signal, lang, has_wallet)
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)
    else:
        # No more cached — silent refresh
        await _show_feed(query, ctx, force_refresh=False)


async def cb_intel_view(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    Callback: intel:view:{sc_idx} — show full signal explanation screen.
    """
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")
    try:
        sc_idx = int(parts[2])
    except (IndexError, ValueError):
        await query.answer("Signal not found.", show_alert=True)
        return

    signal = get_signal(ctx, sc_idx)
    user = await get_user(query.from_user.id)
    lang = (user or {}).get("language", "en")
    has_wallet = bool((user or {}).get("wallet_address"))

    if not signal:
        await query.answer(
            _t("Сигнал устарел — обнови ленту", "Signal expired — refresh feed", lang),
            show_alert=True
        )
        return

    source_texts = {
        "ai_model": {
            "ru": "🤖 <b>AI Model</b>\n\nАлгоритм нашёл расхождение между рыночной ценой и расчётной вероятностью события.",
            "en": "🤖 <b>AI Model</b>\n\nAlgorithm detected a divergence between market price and estimated true probability.",
        },
        "whale_activity": {
            "ru": "🐋 <b>Whale Activity</b>\n\nКрупный трейдер зашёл в позицию. «Умные деньги» часто двигаются раньше рынка.",
            "en": "🐋 <b>Whale Activity</b>\n\nA large trader entered a position. Smart money often moves before the market.",
        },
    }
    src_block = source_texts.get(signal.source, {}).get(lang, "") or \
                source_texts.get(signal.source, {}).get("en", "")

    card   = _build_signal_card_text(signal, lang)
    header = _t("📊 <b>Детали сигнала</b>", "📊 <b>Signal Details</b>", lang)
    lines  = [header, "", card]
    if src_block:
        lines += ["", src_block]

    keyboard = _build_signal_keyboard(sc_idx, signal, lang, has_wallet)
    await query.edit_message_text("\n".join(lines), parse_mode="HTML", reply_markup=keyboard)


async def cb_intel_trade(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    Callback: intel:trade:{sc_idx}:{amount}
    Loads market into mc cache, pre-fills amount, delegates to bet flow.
    """
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")
    try:
        sc_idx = int(parts[2])
        amount = float(parts[3]) if len(parts) > 3 else 25.0
    except (IndexError, ValueError):
        await query.answer("Invalid signal.", show_alert=True)
        return

    signal = get_signal(ctx, sc_idx)
    if not signal:
        user = await get_user(query.from_user.id)
        lang = (user or {}).get("language", "en")
        await query.answer(
            _t("Сигнал устарел — обнови ленту", "Signal expired — refresh feed", lang),
            show_alert=True
        )
        return

    user = await get_user(query.from_user.id)
    lang = (user or {}).get("language", "en")

    # Load market into mc cache
    market = await gamma.get_market(signal.market_id)
    if not market:
        await query.edit_message_text(
            _t("❌ Рынок временно недоступен.", "❌ Market temporarily unavailable.", lang)
        )
        return

    from handlers.markets import _cache_market
    mc_idx = _cache_market(ctx, market)

    # Pre-fill amount and signal context
    ctx.user_data["prefill_amount"] = amount
    ctx.user_data["signal_source"]  = signal.source_label

    # Route to bet flow
    direction_code = "Y" if signal.direction == "YES" else "N"
    query.data = f"b:{direction_code}:{mc_idx}"

    from handlers.betting import cb_bet_start
    return await cb_bet_start(update, ctx)


async def cb_intel_wallet_prompt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    Callback: intel:wallet_prompt:{sc_idx}
    Show wallet onboarding with return-to-signal context.
    """
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")
    sc_idx = int(parts[2]) if len(parts) > 2 else 0
    ctx.user_data["return_after_wallet"] = f"intel:trade:{sc_idx}:25"

    user = await get_user(query.from_user.id)
    lang = (user or {}).get("language", "en")

    text = _t(
        "💳 <b>Для торговли нужен кошелёк</b>\n\n"
        "Создай Polygon-кошелёк за 5 секунд — "
        "после подключения сразу вернёмся к этому сигналу.",
        "💳 <b>Wallet required to trade</b>\n\n"
        "Create a Polygon wallet in 5 seconds — "
        "we'll return to this signal right after.",
        lang
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            _t("🚀 Создать кошелёк", "🚀 Create Wallet", lang),
            callback_data="wallet:create"
        )],
        [InlineKeyboardButton(
            _t("📲 Уже есть кошелёк", "📲 I have one", lang),
            callback_data="wallet:add"
        )],
        [InlineKeyboardButton(
            _t("🔙 К сигналам", "🔙 Back to signals", lang),
            callback_data="intel:feed"
        )],
    ])

    await query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)


# Keep cb_intel_learn for backward compat (now routes to cb_intel_view)
async def cb_intel_learn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Backward-compatible alias — redirects to cb_intel_view."""
    # Re-map query data from intel:learn:N → intel:view:N
    parts = update.callback_query.data.split(":")
    if len(parts) >= 3:
        update.callback_query.data = f"intel:view:{parts[2]}"
    await cb_intel_view(update, ctx)


async def cmd_intel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    Command: /intel — open Intel Feed from a message command.
    """
    user = await get_user(update.effective_user.id)
    lang = (user or {}).get("language", "en")
    has_wallet = bool((user or {}).get("wallet_address"))

    msg = await update.message.reply_html(
        _LOADING.get(lang, _LOADING["en"])
    )

    import asyncio
    markets = await gamma.get_trending_markets(limit=12)
    if not markets:
        markets = await gamma.get_sports_markets(limit=12, tag="sports")

    signals, whale_text = await asyncio.gather(
        signal_pipeline.get_feed(markets, max_signals=8),
        _get_whale_block(lang),
    )

    if not signals:
        empty = _EMPTY_FEED.get(lang, _EMPTY_FEED["en"])
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(_t("🔄 Обновить", "🔄 Refresh", lang), callback_data="intel:refresh")
        ]])
        await msg.edit_text(empty, parse_mode="HTML", reply_markup=keyboard)
        return

    feed_text, primary_idx = _build_feed_text(signals, lang, ctx)

    if whale_text:
        full_text = f"{whale_text}\n\n━━━━\n\n{feed_text}"
    else:
        full_text = feed_text

    keyboard = _build_signal_keyboard(primary_idx, signals[0], lang, has_wallet)
    await msg.edit_text(full_text, parse_mode="HTML", reply_markup=keyboard)
