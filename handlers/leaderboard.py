# PolyScore — Leaderboard handler
# Show top players by total profit

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.database import get_leaderboard, get_user


# ══════════════════════════════════════════════════════════════════════
# Texts (RU / EN)
# ══════════════════════════════════════════════════════════════════════

LEADERBOARD_TITLE_RU = "🏆 <b>Топ трейдеры Polymarket</b>"
LEADERBOARD_TITLE_EN = "🏆 <b>Top Polymarket Traders</b>"

LEADERBOARD_EMPTY_RU = "😔 Пока нет данных о сделках."
LEADERBOARD_EMPTY_EN = "😔 No trading data yet."

LEADERBOARD_YOUR_POSITION_RU = "\n\n📍 <b>Ваша позиция:</b>"
LEADERBOARD_YOUR_POSITION_EN = "\n\n📍 <b>Your Position:</b>"

NOT_ON_LEADERBOARD_RU = "Вы пока не на лидерборде."
NOT_ON_LEADERBOARD_EN = "You're not on the leaderboard yet."


# Medals and rankings
MEDALS = ["🥇", "🥈", "🥉"]


async def format_leaderboard(leaderboard: list[dict], user_id: int, lang: str) -> tuple[str, int]:
    """Format leaderboard text and find user position.

    Returns: (formatted_text, user_position_or_-1)
    """
    if not leaderboard:
        return "", -1

    lines = []
    user_position = -1

    for idx, entry in enumerate(leaderboard, start=1):
        medal = MEDALS[idx - 1] if idx <= 3 else f"{idx}️⃣"
        username = entry.get("username", "Unknown")
        profit = entry.get("total_profit", 0.0)
        win_rate = entry.get("win_rate", 0.0)
        bet_count = entry.get("bet_count", 0)
        entry_user_id = entry.get("user_id")

        if entry_user_id == user_id:
            user_position = idx

        if lang == "ru":
            line = (
                f"{medal} <b>{username}</b>\n"
                f"   💰 +${profit:,.2f}  |  🎯 {win_rate:.1f}%  |  "
                f"🎮 {bet_count} сделок"
            )
        else:
            line = (
                f"{medal} <b>{username}</b>\n"
                f"   💰 +${profit:,.2f}  |  🎯 {win_rate:.1f}%  |  "
                f"🎮 {bet_count} trades"
            )

        lines.append(line)

    return "\n".join(lines), user_position


async def cb_leaderboard(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle /leaderboard command or callback."""
    user = await get_user(update.effective_user.id)
    lang = (user or {}).get("language", "ru")
    user_id = update.effective_user.id

    # Fetch leaderboard from database
    leaderboard = await get_leaderboard(limit=10)

    if not leaderboard:
        text = LEADERBOARD_EMPTY_RU if lang == "ru" else LEADERBOARD_EMPTY_EN
        keyboard = [[
            InlineKeyboardButton("🔙 Назад", callback_data="menu:main") \
            if lang == "ru" else InlineKeyboardButton("🔙 Back", callback_data="menu:main"),
        ]]
    else:
        lb_text, user_pos = await format_leaderboard(leaderboard, user_id, lang)
        title = LEADERBOARD_TITLE_RU if lang == "ru" else LEADERBOARD_TITLE_EN
        text = f"{title}\n\n{lb_text}"

        # Add user position if not on leaderboard
        if user_pos == -1:
            pos_text = LEADERBOARD_YOUR_POSITION_RU if lang == "ru" \
                      else LEADERBOARD_YOUR_POSITION_EN
            pos_msg = NOT_ON_LEADERBOARD_RU if lang == "ru" \
                     else NOT_ON_LEADERBOARD_EN
            text += f"{pos_text}\n{pos_msg}"
        else:
            pos_text = LEADERBOARD_YOUR_POSITION_RU if lang == "ru" \
                      else LEADERBOARD_YOUR_POSITION_EN
            text += f"{pos_text}\n#{user_pos}"

        keyboard = [[
            InlineKeyboardButton("🔙 Назад", callback_data="menu:main") \
            if lang == "ru" else InlineKeyboardButton("🔙 Back", callback_data="menu:main"),
        ]]

    if update.message:
        await update.message.reply_html(
            text, reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            text, parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
