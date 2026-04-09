# PolyScore — Парлей-билдер
# Создание мульти-ставок из 2-5 исходов
# ОБНОВЛЕНО: использует кеш ctx.bot_data["mc"], короткие callback_data

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import io
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.polymarket import gamma, price_to_american_odds
from services.database import get_user, save_parlay
from utils.bet_slip import create_parlay_slip
from config import MAX_PARLAY_LEGS


def _cache_market(ctx: ContextTypes.DEFAULT_TYPE, market: dict) -> int:
    """Сохранить рынок в кеш и вернуть короткий числовой ключ."""
    if "mc" not in ctx.bot_data:
        ctx.bot_data["mc"] = {}
        ctx.bot_data["mc_next"] = 0

    slug = market.get("slug", "")
    for k, v in ctx.bot_data["mc"].items():
        if v.get("slug") == slug and slug:
            ctx.bot_data["mc"][k] = market
            return k

    idx = ctx.bot_data["mc_next"]
    ctx.bot_data["mc"][idx] = market
    ctx.bot_data["mc_next"] = idx + 1

    if len(ctx.bot_data["mc"]) > 200:
        oldest = sorted(ctx.bot_data["mc"].keys())[:100]
        for k in oldest:
            del ctx.bot_data["mc"][k]

    return idx


async def cb_parlay_new(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Начать новый парлей."""
    query = update.callback_query
    await query.answer()

    # Сбрасываем парлей
    ctx.user_data["parlay_legs"] = []

    user = await get_user(query.from_user.id)
    lang = (user or {}).get("language", "ru")

    if lang == "ru":
        text = (
            "🎯 <b>Парлей-билдер</b>\n\n"
            f"Добавь от 2 до {MAX_PARLAY_LEGS} исходов.\n\n"
            "Как работает парлей:\n"
            "• Выбираешь несколько рынков\n"
            "• Коэффициенты перемножаются\n"
            "• Все исходы должны сыграть\n\n"
            "Сначала выбери вид спорта 👇"
        )
        keyboard = [
            [InlineKeyboardButton("⚾ MLB",     callback_data="parlay:pick:baseball"),
             InlineKeyboardButton("🏀 NBA",     callback_data="parlay:pick:basketball")],
            [InlineKeyboardButton("🏒 NHL",     callback_data="parlay:pick:hockey"),
             InlineKeyboardButton("🥊 UFC",     callback_data="parlay:pick:mma")],
            [InlineKeyboardButton("🔥 Горячие", callback_data="parlay:pick:trending")],
            [InlineKeyboardButton("❌ Отмена",  callback_data="menu:main")],
        ]
    else:
        text = (
            "🎯 <b>Parlay Builder</b>\n\n"
            f"Add 2 to {MAX_PARLAY_LEGS} outcomes.\n\n"
            "How parlays work:\n"
            "• Pick multiple markets\n"
            "• Odds multiply together\n"
            "• All outcomes must win\n\n"
            "Pick a sport first 👇"
        )
        keyboard = [
            [InlineKeyboardButton("⚾ MLB",      callback_data="parlay:pick:baseball"),
             InlineKeyboardButton("🏀 NBA",      callback_data="parlay:pick:basketball")],
            [InlineKeyboardButton("🏒 NHL",      callback_data="parlay:pick:hockey"),
             InlineKeyboardButton("🥊 UFC",      callback_data="parlay:pick:mma")],
            [InlineKeyboardButton("🔥 Trending", callback_data="parlay:pick:trending")],
            [InlineKeyboardButton("❌ Cancel",   callback_data="menu:main")],
        ]

    await query.edit_message_text(
        text, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def cb_parlay_pick_tag(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    Callback: parlay:pick:{tag}
    Показывает рынки для выбора ноги парлея.
    Используем кеш и extract_prices().
    """
    query = update.callback_query
    await query.answer("⏳ Загружаю…")

    tag  = query.data.split(":", 2)[2]
    user = await get_user(query.from_user.id)
    lang = (user or {}).get("language", "ru")

    if tag == "trending":
        markets = await gamma.get_trending_markets(limit=8)
    else:
        markets = await gamma.get_sports_markets(limit=8, tag=tag)

    if not markets:
        markets = await gamma.get_trending_markets(limit=8)

    legs = ctx.user_data.get("parlay_legs", [])

    header_text = "🎯 <b>Выбери исход для парлея</b>\n" if lang == "ru" \
                  else "🎯 <b>Pick an outcome for your parlay</b>\n"

    lines = [header_text]
    buttons = []

    for i, m in enumerate(markets[:8]):
        # Кешируем рынок и получаем короткий idx
        idx = _cache_market(ctx, m)

        q = m.get("question", m.get("title", "—"))
        yes_p, no_p = gamma.extract_prices(m)

        if len(q) > 45:
            q_short = q[:42] + "…"
        else:
            q_short = q

        lines.append(f"{i+1}. {q_short}  YES={yes_p:.0%}")

        yes_odds = price_to_american_odds(yes_p)
        no_odds  = price_to_american_odds(no_p)

        # Короткие callback: pl:{idx}:Y и pl:{idx}:N (максимум ~10 байт)
        buttons.append([
            InlineKeyboardButton(
                f"{i+1}. YES {yes_p:.0%} ({yes_odds})",
                callback_data=f"pl:{idx}:Y"
            ),
            InlineKeyboardButton(
                f"NO {no_p:.0%} ({no_odds})",
                callback_data=f"pl:{idx}:N"
            ),
        ])

    # Показать текущие ноги
    if legs:
        lines.append(f"\n✅ Уже выбрано {len(legs)} / {MAX_PARLAY_LEGS}:")
        for j, leg in enumerate(legs, 1):
            lines.append(f"  {j}. {leg['outcome']} — {leg['question'][:35]}…")

    text = "\n".join(lines)
    buttons.append([
        InlineKeyboardButton(
            "✅ Готово, ввести сумму" if lang == "ru" else "✅ Done, enter amount",
            callback_data="parlay:amount"
        )
    ])
    buttons.append([
        InlineKeyboardButton("❌ Сбросить" if lang == "ru" else "❌ Reset",
                             callback_data="parlay:new"),
    ])

    await query.edit_message_text(
        text, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def cb_parlay_add_leg(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    Callback: pl:{idx}:Y или pl:{idx}:N — добавить ногу в парлей из кеша.
    Также обрабатывает pl:{idx} (без outcome) — по умолчанию YES.
    """
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")
    # pl:{idx} или pl:{idx}:Y/N
    idx = int(parts[1])
    outcome = "YES"
    if len(parts) >= 3:
        outcome = "YES" if parts[2] == "Y" else "NO"

    user = await get_user(query.from_user.id)
    lang = (user or {}).get("language", "ru")

    # Получаем рынок из кеша
    market = ctx.bot_data.get("mc", {}).get(idx, {})
    if not market:
        await query.answer("❌ Рынок не найден. Обнови список.", show_alert=True)
        return

    question = market.get("question", market.get("title", str(idx)))
    cond_id  = market.get("conditionId", market.get("id", str(idx)))
    yes_p, no_p = gamma.extract_prices(market)
    price = yes_p if outcome == "YES" else no_p

    legs = ctx.user_data.setdefault("parlay_legs", [])

    # Проверяем дубли (по idx)
    existing_ids = [l.get("idx") for l in legs]
    if idx in existing_ids:
        msg = "⚠️ Этот рынок уже в парлее!" if lang == "ru" \
              else "⚠️ This market is already in the parlay!"
        await query.answer(msg, show_alert=True)
        return

    if len(legs) >= MAX_PARLAY_LEGS:
        msg = f"⚠️ Максимум {MAX_PARLAY_LEGS} ног в парлее" if lang == "ru" \
              else f"⚠️ Maximum {MAX_PARLAY_LEGS} legs per parlay"
        await query.answer(msg, show_alert=True)
        return

    legs.append({
        "idx":      idx,
        "cond_id":  cond_id,
        "question": question,
        "outcome":  outcome,
        "price":    price,
    })
    ctx.user_data["parlay_legs"] = legs

    # Считаем текущий коэффициент
    total_odds = 1.0
    for leg in legs:
        p = leg["price"]
        if p > 0:
            total_odds *= (1 / p)

    msg = (f"✅ Добавлено! В парлее {len(legs)} ног · Коэф: {total_odds:.2f}x" if lang == "ru"
           else f"✅ Added! {len(legs)} legs · Odds: {total_odds:.2f}x")
    await query.answer(msg, show_alert=False)

    # Если минимум 2 ноги — предлагаем оформить
    if len(legs) >= 2:
        lines = [f"🎯 <b>Парлей ({len(legs)} ног)</b>\n"]
        for i, leg in enumerate(legs, 1):
            q_short = leg["question"][:40] + ("…" if len(leg["question"]) > 40 else "")
            lines.append(f"{i}. {leg['outcome']}  {leg['price']:.0%}  — {q_short}")
        lines.append(f"\n📊 Суммарный коэф: <b>{total_odds:.2f}x</b>")

        keyboard = [
            [InlineKeyboardButton(
                "➕ Добавить ещё" if lang == "ru" else "➕ Add more",
                callback_data=f"parlay:pick:sports"
            )],
            [InlineKeyboardButton(
                f"✅ Открыть парлей ({len(legs)} ног)" if lang == "ru"
                else f"✅ Open parlay ({len(legs)} legs)",
                callback_data="parlay:amount"
            )],
            [InlineKeyboardButton(
                "❌ Сбросить" if lang == "ru" else "❌ Reset",
                callback_data="parlay:new"
            )],
        ]

        await query.edit_message_text(
            "\n".join(lines), parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def cb_parlay_amount(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Показать кнопки быстрого выбора суммы."""
    query = update.callback_query
    await query.answer()

    legs = ctx.user_data.get("parlay_legs", [])
    user = await get_user(query.from_user.id)
    lang = (user or {}).get("language", "ru")

    if len(legs) < 2:
        msg = "⚠️ Нужно минимум 2 исхода" if lang == "ru" else "⚠️ Need at least 2 outcomes"
        await query.answer(msg, show_alert=True)
        return

    total_odds = 1.0
    for leg in legs:
        p = leg["price"]
        if p > 0:
            total_odds *= (1 / p)

    if lang == "ru":
        text = (
            f"💵 <b>Сумма парлея</b>\n\n"
            f"Коэффициент: <b>{total_odds:.2f}x</b>\n\n"
            f"При ставке $10 → <b>${10 * total_odds:.2f}</b>\n"
            f"При ставке $25 → <b>${25 * total_odds:.2f}</b>\n"
            f"При ставке $50 → <b>${50 * total_odds:.2f}</b>\n\n"
            f"Выбери сумму:"
        )
    else:
        text = (
            f"💵 <b>Parlay Amount</b>\n\n"
            f"Combined odds: <b>{total_odds:.2f}x</b>\n\n"
            f"$10 bet → <b>${10 * total_odds:.2f}</b>\n"
            f"$25 bet → <b>${25 * total_odds:.2f}</b>\n"
            f"$50 bet → <b>${50 * total_odds:.2f}</b>\n\n"
            f"Choose amount:"
        )

    keyboard = [
        [InlineKeyboardButton("$5",  callback_data="parlay:place:5"),
         InlineKeyboardButton("$10", callback_data="parlay:place:10"),
         InlineKeyboardButton("$25", callback_data="parlay:place:25")],
        [InlineKeyboardButton("$50", callback_data="parlay:place:50"),
         InlineKeyboardButton("$100",callback_data="parlay:place:100")],
        [InlineKeyboardButton("❌ Отмена" if lang == "ru" else "❌ Cancel",
                              callback_data="parlay:new")],
    ]

    await query.edit_message_text(
        text, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def cb_parlay_place(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    Callback: parlay:place:{amount}
    Разместить парлей.
    """
    query  = update.callback_query
    await query.answer()

    amount = float(query.data.split(":")[2])
    legs   = ctx.user_data.get("parlay_legs", [])
    user   = await get_user(query.from_user.id)
    lang   = (user or {}).get("language", "ru")

    if not legs or len(legs) < 2:
        await query.edit_message_text("❌ Парлей пуст. Начни заново.")
        return

    # Считаем total odds
    total_odds = 1.0
    for leg in legs:
        p = leg["price"]
        if p > 0:
            total_odds *= (1 / p)

    potential = amount * total_odds

    # Сохраняем в БД
    parlay_id = await save_parlay(
        user_id      = query.from_user.id,
        legs         = legs,
        total_odds   = total_odds,
        total_amount = amount,
    )

    # Генерируем парлей-карточку
    username = query.from_user.username or str(query.from_user.id)
    slip_img = create_parlay_slip(
        legs     = legs,
        amount   = amount,
        username = username,
    )

    if lang == "ru":
        caption = (
            f"🎉 <b>Парлей размещён!</b>\n\n"
            f"Ног: <b>{len(legs)}</b>  ·  Коэф: <b>{total_odds:.2f}x</b>\n"
            f"Сумма: <b>${amount:.2f}</b>  →  Выигрыш: <b>${potential:.2f}</b>\n\n"
            f"ID: <code>{parlay_id}</code>\n\n"
            f"Удачи! 🤞 Поделись карточкой ☝️"
        )
    else:
        caption = (
            f"🎉 <b>Parlay placed!</b>\n\n"
            f"Legs: <b>{len(legs)}</b>  ·  Odds: <b>{total_odds:.2f}x</b>\n"
            f"Stake: <b>${amount:.2f}</b>  →  Payout: <b>${potential:.2f}</b>\n\n"
            f"ID: <code>{parlay_id}</code>\n\n"
            f"Good luck! 🤞 Share the card ☝️"
        )

    keyboard = [[
        InlineKeyboardButton("📊 Портфель" if lang == "ru" else "📊 Portfolio",
                             callback_data="portfolio"),
        InlineKeyboardButton("🎯 Ещё парлей" if lang == "ru" else "🎯 New parlay",
                             callback_data="parlay:new"),
    ]]

    await query.message.reply_photo(
        photo   = io.BytesIO(slip_img),
        caption = caption,
        parse_mode = "HTML",
        reply_markup = InlineKeyboardMarkup(keyboard)
    )
    await query.edit_message_text("✅ Парлей размещён!")
    ctx.user_data.pop("parlay_legs", None)
