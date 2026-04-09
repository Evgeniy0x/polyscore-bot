# PolyScore — Copy Trading Handlers
# Интерфейс для следования за трейдерами и копирования их сделок

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import POLY_API_KEY
from services.database import (
    get_user,
    follow_trader,
    unfollow_trader,
    get_followed_traders,
    toggle_copy_trading,
)
from services.copy_trading import copy_trading_service
from services.polymarket import gamma


# ══════════════════════════════════════════════════════════════════════
# Тексты и переводы (Russian + English)
# ══════════════════════════════════════════════════════════════════════

TEXTS = {
    "ru": {
        "no_wallet": "❌ Сначала подключи кошелёк в /wallet",
        "copy_menu_title": "👤 Копирование сделок",
        "copy_menu_empty": "Ты ещё не следишь за трейдерами.",
        "copy_menu_button": "➕ Найти трейдера",
        "copy_menu_toggle_on": "⏸ Паузировать копирование",
        "copy_menu_toggle_off": "▶️ Возобновить копирование",
        "search_title": "🔍 Лучшие трейдеры",
        "search_empty": "Нет трейдеров в топе.",
        "search_footer": "Выбери трейдера чтобы следить за ним.",
        "follow_ask_pct": "Какой процент от своего баланса копировать?\n(1–100%, рекомендуем 10–25%)",
        "follow_success": "✅ Ты теперь следишь за {trader}",
        "follow_exists": "⚠️ Ты уже следишь за этим трейдером",
        "unfollow_success": "✅ Ты больше не следишь за {trader}",
        "invalid_pct": "❌ Введи число от 1 до 100",
        "trader_card": """👤 {name} ({addr})
📊 30-день: {pnl}
💰 Копирование: {pct}%
Статус: {status}""",
        "status_active": "🟢 Активно",
        "status_paused": "🟡 На паузе",
        "pause_button": "⏸ Паузировать",
        "unpause_button": "▶️ Возобновить",
        "unfollow_button": "🗑 Отписаться",
        "stats_button": "📊 Статистика",
        "back_button": "◀ Назад",
    },
    "en": {
        "no_wallet": "❌ Connect your wallet first in /wallet",
        "copy_menu_title": "👤 Copy Trading",
        "copy_menu_empty": "You don't follow any traders yet.",
        "copy_menu_button": "➕ Find Trader",
        "copy_menu_toggle_on": "⏸ Pause Copying",
        "copy_menu_toggle_off": "▶️ Resume Copying",
        "search_title": "🔍 Top Traders",
        "search_empty": "No traders in top.",
        "search_footer": "Select a trader to follow.",
        "follow_ask_pct": "What percentage of your balance to copy?\n(1–100%, we recommend 10–25%)",
        "follow_success": "✅ You now follow {trader}",
        "follow_exists": "⚠️ You already follow this trader",
        "unfollow_success": "✅ You no longer follow {trader}",
        "invalid_pct": "❌ Enter a number from 1 to 100",
        "trader_card": """👤 {name} ({addr})
📊 30-day: {pnl}
💰 Copying: {pct}%
Status: {status}""",
        "status_active": "🟢 Active",
        "status_paused": "🟡 Paused",
        "pause_button": "⏸ Pause",
        "unpause_button": "▶️ Resume",
        "unfollow_button": "🗑 Unfollow",
        "stats_button": "📊 Stats",
        "back_button": "◀ Back",
    }
}


def t(user_language: str, key: str) -> str:
    """Get text in user's language (fallback to English)."""
    lang = user_language if user_language in TEXTS else "en"
    return TEXTS[lang].get(key, TEXTS["en"].get(key, ""))


# ══════════════════════════════════════════════════════════════════════
# Handlers
# ══════════════════════════════════════════════════════════════════════

async def cb_copy_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    Главное меню копирования (callback copy:menu).
    Показывает список следимых трейдеров с их статистикой.
    """
    user_id = update.effective_user.id
    user = await get_user(user_id)

    if not user:
        await update.callback_query.answer(t("en", "no_wallet"), show_alert=True)
        return

    lang = user.get("language", "ru")

    # Проверить кошелёк
    if not user.get("wallet_address") or not POLY_API_KEY:
        await update.callback_query.answer(t(lang, "no_wallet"), show_alert=True)
        return

    # Получить следимых трейдеров
    followed = await get_followed_traders(user_id)

    # Построить сообщение
    if not followed:
        text = f"<b>{t(lang, 'copy_menu_title')}</b>\n\n{t(lang, 'copy_menu_empty')}"
        keyboard = [
            [InlineKeyboardButton(t(lang, "copy_menu_button"), callback_data="copy:search")],
            [InlineKeyboardButton(t(lang, "back_button"), callback_data="menu:main")],
        ]
    else:
        lines = [f"<b>{t(lang, 'copy_menu_title')}</b>"]
        lines.append(f"Ты следишь за {len(followed)} трейдерами:")
        lines.append("")

        for trader in followed:
            addr_short = f"{trader['trader_address'][:6]}...{trader['trader_address'][-4:]}"
            name = trader.get("trader_name", "Unknown")
            pct = trader.get("copy_pct", 10)
            status = t(lang, "status_active") if trader.get("active") else t(lang, "status_paused")

            lines.append(f"👤 {name} ({addr_short})")
            lines.append(f"   📊 PnL: N/A | 💰 Копия: {pct}% | {status}")
            lines.append("")

        text = "\n".join(lines)

        # Кнопки для каждого трейдера
        keyboard = []
        for trader in followed:
            addr = trader["trader_address"]
            name = trader.get("trader_name", "Unknown")[:15]
            keyboard.append([
                InlineKeyboardButton(
                    f"⚙️ {name}",
                    callback_data=f"copy:trader:{addr}"
                ),
            ])

        # Кнопки внизу
        keyboard.append([InlineKeyboardButton(t(lang, "copy_menu_button"), callback_data="copy:search")])
        keyboard.append([InlineKeyboardButton(t(lang, "back_button"), callback_data="menu:main")])

    keyboard_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=keyboard_markup,
            parse_mode=ParseMode.HTML,
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=keyboard_markup,
            parse_mode=ParseMode.HTML,
        )


async def cb_copy_search(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    Поиск трейдеров (callback copy:search).
    Показывает топ-трейдеров из лидерборда для следования.
    """
    user_id = update.effective_user.id
    user = await get_user(user_id)

    if not user:
        await update.callback_query.answer(t("en", "no_wallet"), show_alert=True)
        return

    lang = user.get("language", "ru")

    # Здесь можно получить топ-трейдеров из публичного API
    # Для демонстрации, используем mock-данные
    # В реальности: fetch from Polymarket leaderboard API

    text = f"""<b>{t(lang, 'search_title')}</b>

{t(lang, 'search_footer')}

(Интеграция с публичным лидербордом API)"""

    keyboard = [
        [InlineKeyboardButton(t(lang, "back_button"), callback_data="copy:menu")],
    ]
    keyboard_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text,
        reply_markup=keyboard_markup,
        parse_mode=ParseMode.HTML,
    )


async def cb_copy_follow(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    Следить за трейдером (callback copy:follow:{address}).
    Запрашивает процент копирования и сохраняет подписку.
    """
    user_id = update.effective_user.id
    user = await get_user(user_id)

    if not user:
        await update.callback_query.answer(t("en", "no_wallet"), show_alert=True)
        return

    lang = user.get("language", "ru")

    # Извлечь адрес из callback_data
    data = update.callback_query.data  # copy:follow:{address}
    parts = data.split(":")
    if len(parts) < 3:
        await update.callback_query.answer("❌ Invalid data", show_alert=True)
        return

    trader_address = ":".join(parts[2:])  # Поддержать 0x-адреса с двоеточиями

    # Проверить, уже ли следим
    followed = await get_followed_traders(user_id)
    if any(f["trader_address"] == trader_address for f in followed):
        await update.callback_query.answer(t(lang, "follow_exists"), show_alert=True)
        return

    # Сохранить адрес в контексте
    ctx.user_data["copy_follow_address"] = trader_address
    ctx.user_data["copy_follow_step"] = "wait_pct"

    text = t(lang, "follow_ask_pct")
    await update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML)


async def cb_copy_unfollow(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    Отписаться от трейдера (callback copy:unfollow:{address}).
    """
    user_id = update.effective_user.id
    user = await get_user(user_id)

    if not user:
        await update.callback_query.answer(t("en", "no_wallet"), show_alert=True)
        return

    lang = user.get("language", "ru")

    # Извлечь адрес
    data = update.callback_query.data
    parts = data.split(":")
    if len(parts) < 3:
        await update.callback_query.answer("❌ Invalid data", show_alert=True)
        return

    trader_address = ":".join(parts[2:])

    # Отписаться
    await unfollow_trader(user_id, trader_address)
    await update.callback_query.answer(
        t(lang, "unfollow_success").format(trader=trader_address[:10]),
        show_alert=True,
    )

    # Вернуться в меню
    await cb_copy_menu(update, ctx)


async def cb_copy_toggle(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    Включить/выключить копирование (callback copy:toggle).
    Переключает active флаг для всех следимых трейдеров пользователя.
    """
    user_id = update.effective_user.id
    user = await get_user(user_id)

    if not user:
        await update.callback_query.answer(t("en", "no_wallet"), show_alert=True)
        return

    lang = user.get("language", "ru")

    # Получить текущее состояние
    followed = await get_followed_traders(user_id)
    if not followed:
        await update.callback_query.answer("❌ No traders to toggle", show_alert=True)
        return

    # Определить новое состояние (если хотя бы один активен, выключить все)
    all_active = all(f.get("active") for f in followed)
    new_state = not all_active

    # Обновить
    await toggle_copy_trading(user_id, new_state)

    status_text = t(lang, "status_active") if new_state else t(lang, "status_paused")
    await update.callback_query.answer(
        f"✅ Копирование: {status_text}",
        show_alert=True,
    )

    # Вернуться в меню
    await cb_copy_menu(update, ctx)


async def message_copy_pct_input(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    Обработать ввод процента копирования после нажатия копирования трейдера.
    """
    user_id = update.effective_user.id
    user = await get_user(user_id)

    if not user:
        return

    lang = user.get("language", "ru")

    # Проверить, находимся ли в режиме ввода %
    if ctx.user_data.get("copy_follow_step") != "wait_pct":
        return

    # Парсить ввод
    text = update.message.text.strip()
    try:
        copy_pct = float(text)
        if not (1 <= copy_pct <= 100):
            raise ValueError("Out of range")
    except (ValueError, TypeError):
        await update.message.reply_text(t(lang, "invalid_pct"))
        return

    # Получить адрес из контекста
    trader_address = ctx.user_data.get("copy_follow_address", "")
    if not trader_address:
        await update.message.reply_text("❌ Error: trader address not found")
        return

    # Сохранить подписку
    await follow_trader(user_id, trader_address, copy_pct, trader_name="")
    await update.message.reply_text(
        t(lang, "follow_success").format(trader=trader_address[:10]),
        parse_mode=ParseMode.HTML,
    )

    # Очистить контекст
    ctx.user_data.pop("copy_follow_address", None)
    ctx.user_data.pop("copy_follow_step", None)

    # Вернуться в меню
    await cb_copy_menu(update, ctx)


# ══════════════════════════════════════════════════════════════════════
# Регистрация handlers
# ══════════════════════════════════════════════════════════════════════

def setup_copy_trading_handlers(app):
    """
    Зарегистрировать handlers для copy trading в приложении.

    Использование в main bot:
        from handlers.copy_trading import setup_copy_trading_handlers
        setup_copy_trading_handlers(app)
    """
    from telegram.ext import CallbackQueryHandler, MessageHandler, filters

    # Callback handlers
    app.add_handler(CallbackQueryHandler(cb_copy_menu, pattern="^copy:menu$"))
    app.add_handler(CallbackQueryHandler(cb_copy_search, pattern="^copy:search$"))
    app.add_handler(CallbackQueryHandler(cb_copy_follow, pattern="^copy:follow:"))
    app.add_handler(CallbackQueryHandler(cb_copy_unfollow, pattern="^copy:unfollow:"))
    app.add_handler(CallbackQueryHandler(cb_copy_toggle, pattern="^copy:toggle$"))

    # Message handler для ввода %
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_copy_pct_input))

    print("[Handlers] Copy trading handlers registered")
