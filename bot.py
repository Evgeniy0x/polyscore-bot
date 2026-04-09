#!/usr/bin/env python3
# PolyScore — Главный файл бота
# Все handlers, конфигурация, запуск в одном месте.
# Запуск: python bot.py

import asyncio
import logging
import sys
import os
import io
import signal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, filters, ContextTypes
)

from config import BOT_TOKEN
from services.database import (
    init_db, get_user, create_user, set_language,
    get_user_stats, get_user_bets, get_user_parlays, get_watchlist
)
from handlers.start import (
    cmd_start, cmd_help, cmd_language,
    cb_language, cb_main_menu, WELCOME, MAIN_MENU
)
from handlers.markets import (
    cmd_sports, cb_sports_menu, cb_markets_menu, cb_tag_markets,
    cb_trending, cb_market_detail, cb_watchlist_add,
    _cache_market, _get_cached
)
from handlers.betting import (
    cb_bet_start, msg_bet_amount, cb_bet_confirm,
    cb_bet_cancel, cb_bet_quick, WAIT_AMOUNT,
    cb_sell_start, cb_sell_confirm, cb_sell_cancel,
)
from handlers.parlay import (
    cb_parlay_new, cb_parlay_pick_tag, cb_parlay_add_leg,
    cb_parlay_amount, cb_parlay_place
)
from handlers.portfolio import (
    cb_portfolio, cb_portfolio_all, cb_portfolio_refresh, cb_watchlist,
    cb_ai_morning, cmd_ai, cb_ai_market, cb_ai_edge
)
from handlers.wallet import (
    cmd_wallet, cb_wallet_guide, cb_wallet_add, cb_wallet_create,
    msg_wallet_address, cb_wallet_cancel, cb_wallet_status, WAIT_WALLET_ADDRESS
)
from handlers.leaderboard import cb_leaderboard
from handlers.academy import setup_academy_handlers
from handlers.copy_trading import (
    cb_copy_menu, cb_copy_search, cb_copy_follow,
    cb_copy_unfollow, cb_copy_toggle, setup_copy_trading_handlers
)
from handlers.alerts import (
    cb_alerts, cb_alert_delete, cb_alert_add,
    cb_alert_set, alerts_worker
)
from handlers.settings import (
    cb_settings as cb_settings_full,
    cb_settings_notifications, cb_settings_notif_level, cb_lang_picker
)
from handlers.intel import (
    cmd_intel,
    cb_intel_feed, cb_intel_refresh, cb_intel_skip,
    cb_intel_trade, cb_intel_wallet_prompt, cb_intel_learn,
    cb_intel_view,
)
from services.copy_trading import copy_trading_service
from services.polymarket import gamma
from services.position_sync import position_sync_worker

# ══════════════════════════════════════════════════════════════════════
# Логирование
# ══════════════════════════════════════════════════════════════════════

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)],
)
logging.getLogger("telegram.ext").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger("PolyScore")


# ══════════════════════════════════════════════════════════════════════
# ERROR HANDLER
# ══════════════════════════════════════════════════════════════════════

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    from telegram.error import Conflict
    err = context.error
    err_str = str(err).lower()

    # Conflict = другой экземпляр бота уже запущен — немедленно завершаем
    if isinstance(err, Conflict):
        logger.critical("💥 Conflict: другой экземпляр бота уже запущен! Завершаю этот процесс.")
        os.kill(os.getpid(), signal.SIGTERM)
        return

    # Безобидные ошибки — игнорируем
    if any(s in err_str for s in [
        "query is too old", "query id is invalid",
        "message is not modified", "message to edit not found",
    ]):
        return

    logger.error("❌ Unhandled exception:", exc_info=err)

    try:
        if isinstance(update, Update):
            if update.callback_query:
                await update.callback_query.answer(
                    "⚠️ Ошибка. Попробуй /start", show_alert=True
                )
            elif update.message:
                await update.message.reply_text("⚠️ Ошибка. Попробуй /start")
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════
# Fallback для устаревших кнопок
# ══════════════════════════════════════════════════════════════════════

async def cb_unknown_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    logger.warning(f"Unknown callback: {query.data!r}")
    try:
        await query.answer("⏳ Устаревшая кнопка. Нажми /start", show_alert=True)
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════
# Settings и Help callbacks (определены ДО main!)
# ══════════════════════════════════════════════════════════════════════

# cb_settings — делегируем в handlers/settings.py (полная версия)
async def cb_settings(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await cb_settings_full(update, ctx)


# cb_alerts импортируется из handlers.alerts


async def cb_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = await get_user(query.from_user.id)
    lang = (user or {}).get("language", "ru")

    if lang == "ru":
        text = (
            "❓ <b>Как пользоваться PolyScore</b>\n\n"
            "🤖 <b>AutoTrade</b> — главная функция:\n"
            "  1. Подключи кошелёк → пополни USDC\n"
            "  2. Включи AutoTrade → алгоритм торгует 24/7\n"
            "  3. Следи за P&L в реальном времени\n"
            "  💰 Мы берём 20% только с прибыли\n\n"
            "📊 <b>Торгуй сам</b>:\n"
            "  ⚾ Спорт, крипта, политика\n"
            "  🎯 Парлеи, AI-прогнозы, алерты\n\n"
            "/start — главное меню\n"
            "/wallet — кошелёк\n"
            "/ai — AI-брифинг"
        )
    else:
        text = (
            "❓ <b>How to use PolyScore</b>\n\n"
            "🤖 <b>AutoTrade</b> — main feature:\n"
            "  1. Connect wallet → fund with USDC\n"
            "  2. Enable AutoTrade → algorithm trades 24/7\n"
            "  3. Watch your P&L in real time\n"
            "  💰 We take 20% only from profit\n\n"
            "📊 <b>Trade yourself</b>:\n"
            "  ⚾ Sports, crypto, politics\n"
            "  🎯 Parlays, AI picks, alerts\n\n"
            "/start — main menu\n"
            "/wallet — wallet\n"
            "/ai — AI briefing"
        )

    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="menu:main")]]
    await query.edit_message_text(
        text, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ══════════════════════════════════════════════════════════════════════
# Команды-обёртки для message-based вызовов
# ══════════════════════════════════════════════════════════════════════

async def cmd_trending(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Команда /trending через message."""
    user = await get_user(update.effective_user.id)
    if not user:
        user = await create_user(update.effective_user.id,
                                  update.effective_user.username or "")
    lang = (user or {}).get("language", "ru")

    markets = await gamma.get_trending_markets(limit=8)
    if not markets:
        await update.message.reply_text("😔 Нет горячих рынков.")
        return

    from services.polymarket import format_volume, price_to_american_odds
    from config import SPORT_EMOJI

    header = "🔥 <b>Горячие рынки</b>\n\n" if lang == "ru" \
             else "🔥 <b>Trending Markets</b>\n\n"
    lines = [header]
    cached_ids = []

    for m in markets[:8]:
        idx = _cache_market(ctx, m)
        cached_ids.append(idx)
        q = m.get("question", m.get("title", "—"))
        yes_p, _ = gamma.extract_prices(m)
        v24 = float(m.get("volume24hr", 0) or 0)
        if len(q) > 50:
            q = q[:47] + "…"
        lines.append(f"🏆 {q}")
        lines.append(f"   YES <b>{yes_p:.0%}</b>  ·  {format_volume(v24)}")
        lines.append("")

    keyboard = []
    for i, idx in enumerate(cached_ids):
        m = markets[i] if i < len(markets) else {}
        q_btn = m.get("question", m.get("title", ""))[:30] + "…"
        keyboard.append([InlineKeyboardButton(
            f"{i+1}. {q_btn}", callback_data=f"m:{idx}"
        )])
    keyboard.append([
        InlineKeyboardButton("📊 Рынки", callback_data="cat:markets"),
        InlineKeyboardButton("🔙 Меню", callback_data="menu:main"),
    ])

    await update.message.reply_html(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def cmd_portfolio(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Команда /portfolio через message."""
    user = await get_user(update.effective_user.id)
    if not user:
        user = await create_user(update.effective_user.id,
                                  update.effective_user.username or "")
    lang = (user or {}).get("language", "ru")

    stats = await get_user_stats(update.effective_user.id)
    total_bets      = stats.get("total_bets", 0)
    total_invested  = stats.get("total_invested", 0.0)
    total_potential = stats.get("total_potential", 0.0)
    roi = ((total_potential - total_invested) / total_invested * 100) \
          if total_invested > 0 else 0

    text = (
        f"📊 <b>{'Мой портфель' if lang=='ru' else 'My Portfolio'}</b>\n\n"
        f"{'Сделок' if lang=='ru' else 'Trades'}: <b>{total_bets}</b>\n"
        f"{'Вложено' if lang=='ru' else 'Invested'}: <b>${total_invested:.2f}</b>\n"
        f"{'Потенциал' if lang=='ru' else 'Potential'}: <b>${total_potential:.2f}</b>\n"
        f"ROI: <b>{roi:+.1f}%</b>"
    )
    keyboard = [[
        InlineKeyboardButton("📊 К рынкам", callback_data="cat:markets"),
        InlineKeyboardButton("🔙 Меню", callback_data="menu:main"),
    ]]
    await update.message.reply_html(
        text, reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def cmd_parlay(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Команда /parlay через message — редиректим в cb_parlay_new."""
    # cb_parlay_new ожидает callback_query, делаем обёртку
    user = await get_user(update.effective_user.id)
    if not user:
        user = await create_user(update.effective_user.id,
                                  update.effective_user.username or "")
    lang = (user or {}).get("language", "ru")

    text = "🎯 <b>Парлей</b>\n\nВыбери вид спорта для первой ноги:" \
           if lang == "ru" else "🎯 <b>Parlay</b>\n\nChoose sport for first leg:"

    keyboard = [
        [InlineKeyboardButton("⚾ MLB", callback_data="parlay:pick:baseball"),
         InlineKeyboardButton("🏀 NBA", callback_data="parlay:pick:basketball")],
        [InlineKeyboardButton("🏒 NHL", callback_data="parlay:pick:hockey"),
         InlineKeyboardButton("⚽ Soccer", callback_data="parlay:pick:soccer")],
        [InlineKeyboardButton("🏈 NFL", callback_data="parlay:pick:football"),
         InlineKeyboardButton("🥊 UFC", callback_data="parlay:pick:mma")],
        [InlineKeyboardButton("🏆 Все виды", callback_data="parlay:pick:sports")],
        [InlineKeyboardButton("🔙 Назад", callback_data="menu:main")],
    ]
    await update.message.reply_html(
        text, reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ══════════════════════════════════════════════════════════════════════
# Post-init
# ══════════════════════════════════════════════════════════════════════

async def post_init(app: Application):
    await init_db()
    from services.translator import init_translator
    await init_translator()
    logger.info("✅ PolyScore запущен! БД готова.")
    logger.info(f"   BOT_TOKEN:       {'✅' if BOT_TOKEN else '❌ НЕ ЗАДАН'}")
    from config import POLY_API_KEY, POLY_SECRET, POLY_PASSPHRASE, POLY_PRIVATE_KEY
    logger.info(f"   POLY_API_KEY:    {'✅' if POLY_API_KEY else '❌ ПУСТО — бот в DEMO режиме!'}")
    logger.info(f"   POLY_SECRET:     {'✅' if POLY_SECRET else '❌ ПУСТО'}")
    logger.info(f"   POLY_PASSPHRASE: {'✅' if POLY_PASSPHRASE else '❌ ПУСТО'}")
    logger.info(f"   POLY_PRIVATE_KEY:{'✅' if POLY_PRIVATE_KEY else '❌ ПУСТО — подпись ордеров невозможна!'}")
    # Запускаем фоновый мониторинг copy trading
    import asyncio
    asyncio.create_task(copy_trading_service.start_monitoring())
    logger.info("🔄 Copy trading мониторинг запущен")
    asyncio.create_task(alerts_worker(app))
    logger.info("🔔 Alerts воркер запущен")
    asyncio.create_task(position_sync_worker(app))
    logger.info("📊 Position sync воркер запущен")


# ══════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════

def main():
    if not BOT_TOKEN or BOT_TOKEN == "ТВОЙ_BOT_TOKEN_ТУТ":
        print("❌ BOT_TOKEN не задан!")
        sys.exit(1)

    from telegram.request import HTTPXRequest
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .request(HTTPXRequest(connect_timeout=10, read_timeout=30, write_timeout=10))
        .post_init(post_init)
        .build()
    )

    # Error handler
    app.add_error_handler(error_handler)

    # ── ConversationHandler: флоу кошелька ──────────────────────────────
    wallet_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(cb_wallet_add, pattern=r"^wallet:add$")
        ],
        states={
            WAIT_WALLET_ADDRESS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, msg_wallet_address),
                CallbackQueryHandler(cb_wallet_cancel, pattern=r"^wallet:cancel$"),
            ]
        },
        fallbacks=[
            CommandHandler("start", cmd_start),
            CallbackQueryHandler(cb_wallet_cancel, pattern=r"^wallet:cancel$"),
        ],
        per_message=False,
    )

    # ── ConversationHandler: флоу ставки ──────────────────────────────
    bet_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(cb_bet_start, pattern=r"^b:[YN]:\d+$")
        ],
        states={
            WAIT_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, msg_bet_amount),
                CallbackQueryHandler(cb_bet_quick,  pattern=r"^bet:quick:\d+"),
                CallbackQueryHandler(cb_bet_cancel, pattern=r"^bet:cancel$"),
            ]
        },
        fallbacks=[
            CommandHandler("start", cmd_start),
            CallbackQueryHandler(cb_bet_cancel, pattern=r"^bet:cancel$"),
        ],
        per_message=False,
    )

    # ── Команды ───────────────────────────────────────────────────────
    app.add_handler(CommandHandler("start",     cmd_start))
    app.add_handler(CommandHandler("help",      cmd_help))
    app.add_handler(CommandHandler("sports",    cmd_sports))
    app.add_handler(CommandHandler("trending",  cmd_trending))
    app.add_handler(CommandHandler("ai",        cmd_ai))
    app.add_handler(CommandHandler("lang",      cmd_language))
    app.add_handler(CommandHandler("portfolio", cmd_portfolio))
    app.add_handler(CommandHandler("parlay",    cmd_parlay))
    app.add_handler(CommandHandler("wallet",    cmd_wallet))
    app.add_handler(CommandHandler("intel",     cmd_intel))
    app.add_handler(CommandHandler("leaderboard", cb_leaderboard))

    # ConversationHandlers
    app.add_handler(wallet_conv)
    app.add_handler(bet_conv)

    # ── Callback handlers (от специфичных к общим) ────────────────────

    # Навигация
    app.add_handler(CallbackQueryHandler(cb_main_menu, pattern=r"^menu:main$"))
    # lang:picker ДОЛЖЕН быть до lang: (иначе ^lang: поглотит его первым)
    app.add_handler(CallbackQueryHandler(cb_lang_picker,             pattern=r"^lang:picker$"))
    app.add_handler(CallbackQueryHandler(cb_language,                pattern=r"^lang:"))
    app.add_handler(CallbackQueryHandler(cb_settings,                pattern=r"^settings$"))
    app.add_handler(CallbackQueryHandler(cb_settings_notifications,  pattern=r"^settings:notifications$"))
    app.add_handler(CallbackQueryHandler(cb_settings_notif_level,    pattern=r"^settings:notif:"))
    app.add_handler(CallbackQueryHandler(cb_help,      pattern=r"^help$"))
    app.add_handler(CallbackQueryHandler(cb_alerts,       pattern=r"^alerts$"))
    app.add_handler(CallbackQueryHandler(cb_alert_add,    pattern=r"^alert:add:\d+$"))
    app.add_handler(CallbackQueryHandler(cb_alert_set,    pattern=r"^alert:set:"))
    app.add_handler(CallbackQueryHandler(cb_alert_delete, pattern=r"^alert:del:\d+$"))

    # Рынки (все категории + спорт)
    app.add_handler(CallbackQueryHandler(cb_markets_menu,  pattern=r"^cat:markets$"))
    app.add_handler(CallbackQueryHandler(cb_sports_menu,   pattern=r"^cat:sports$"))
    app.add_handler(CallbackQueryHandler(cb_trending,      pattern=r"^cat:trending$"))
    app.add_handler(CallbackQueryHandler(cb_tag_markets,   pattern=r"^tag:"))
    app.add_handler(CallbackQueryHandler(cb_market_detail, pattern=r"^m:\d+$"))
    app.add_handler(CallbackQueryHandler(cb_watchlist_add, pattern=r"^w:\d+$"))

    # Ставки
    app.add_handler(CallbackQueryHandler(cb_bet_confirm, pattern=r"^bet:confirm$"))
    app.add_handler(CallbackQueryHandler(cb_bet_cancel,  pattern=r"^bet:cancel$"))
    app.add_handler(CallbackQueryHandler(cb_bet_quick,   pattern=r"^bet:quick:\d+"))

    # Продажа позиций (SELL)
    app.add_handler(CallbackQueryHandler(cb_sell_start,   pattern=r"^sell:\d+$"))
    app.add_handler(CallbackQueryHandler(cb_sell_confirm, pattern=r"^sell:confirm$"))
    app.add_handler(CallbackQueryHandler(cb_sell_cancel,  pattern=r"^sell:cancel$"))

    # Парлеи
    app.add_handler(CallbackQueryHandler(cb_parlay_new,      pattern=r"^parlay:new$"))
    app.add_handler(CallbackQueryHandler(cb_parlay_pick_tag, pattern=r"^parlay:pick:"))
    app.add_handler(CallbackQueryHandler(cb_parlay_add_leg,  pattern=r"^pl:\d+"))
    app.add_handler(CallbackQueryHandler(cb_parlay_amount,   pattern=r"^parlay:amount$"))
    app.add_handler(CallbackQueryHandler(cb_parlay_place,    pattern=r"^parlay:place:\d+$"))

    # Портфель
    app.add_handler(CallbackQueryHandler(cb_portfolio,         pattern=r"^portfolio$"))
    app.add_handler(CallbackQueryHandler(cb_portfolio_refresh, pattern=r"^portfolio:refresh$"))
    app.add_handler(CallbackQueryHandler(cb_portfolio_all,     pattern=r"^portfolio:(all|parlays)$"))
    app.add_handler(CallbackQueryHandler(cb_watchlist,         pattern=r"^watchlist$"))

    # AI
    app.add_handler(CallbackQueryHandler(cb_ai_morning, pattern=r"^ai:morning$"))
    app.add_handler(CallbackQueryHandler(cb_ai_market,  pattern=r"^ai:\d+$"))
    app.add_handler(CallbackQueryHandler(cb_ai_edge,    pattern=r"^edge:\d+$"))

    # Wallet
    app.add_handler(CallbackQueryHandler(cb_wallet_create, pattern=r"^wallet:create$"))
    app.add_handler(CallbackQueryHandler(cb_wallet_status, pattern=r"^wallet:status$"))
    app.add_handler(CallbackQueryHandler(cb_wallet_guide,  pattern=r"^wallet:guide$"))
    app.add_handler(CallbackQueryHandler(cmd_wallet,       pattern=r"^wallet:main$"))

    # Leaderboard
    app.add_handler(CallbackQueryHandler(cb_leaderboard, pattern=r"^leaderboard$"))

    # Intel Mode
    app.add_handler(CallbackQueryHandler(cb_intel_feed,          pattern=r"^intel:feed$"))
    app.add_handler(CallbackQueryHandler(cb_intel_refresh,       pattern=r"^intel:refresh$"))
    app.add_handler(CallbackQueryHandler(cb_intel_skip,          pattern=r"^intel:skip:\d+$"))
    app.add_handler(CallbackQueryHandler(cb_intel_trade,         pattern=r"^intel:trade:\d+(:\d+)?$"))
    app.add_handler(CallbackQueryHandler(cb_intel_view,          pattern=r"^intel:view:\d+$"))
    app.add_handler(CallbackQueryHandler(cb_intel_wallet_prompt, pattern=r"^intel:wallet_prompt:\d+$"))
    app.add_handler(CallbackQueryHandler(cb_intel_learn,         pattern=r"^intel:learn:\d+$"))

    # Academy
    setup_academy_handlers(app)

    # Copy Trading
    setup_copy_trading_handlers(app)

    # Fallback: любой неизвестный callback
    app.add_handler(CallbackQueryHandler(cb_unknown_callback))

    # ── Запуск ────────────────────────────────────────────────────────
    logger.info("🚀 Запускаю polling…")
    app.run_polling(
        allowed_updates=["message", "callback_query"],
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    import asyncio
    import fcntl

    # Защита от двойного запуска — только один экземпляр бота
    _lock_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".bot.lock")
    _lock_file = open(_lock_path, "w")
    try:
        fcntl.flock(_lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("❌ Бот уже запущен! Убей старый процесс: pkill -9 -f bot.py")
        sys.exit(1)

    asyncio.set_event_loop(asyncio.new_event_loop())
    main()
