# PolyScore — Портфель, история ставок, AI-прогнозы
# ОБНОВЛЕНО: реальные позиции с Polymarket data-api + локальная история ставок

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import asyncio
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.database import get_user, get_user_bets, get_user_stats, get_user_parlays, get_watchlist
from services.polymarket import gamma
from services.ai_service import (
    get_sport_prediction, get_morning_briefing,
    explain_market, analyze_edge
)
from services.position_sync import get_positions, enrich_position


# ══════════════════════════════════════════════════════════════════════
# Портфель
# ══════════════════════════════════════════════════════════════════════

async def cb_portfolio(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Показать портфель пользователя.

    Если кошелёк подключён — показываем РЕАЛЬНЫЕ позиции с Polymarket data-api
    (current_value, entry_value, P&L).
    Если нет — показываем локальную историю ставок из БД как раньше.
    """
    query = update.callback_query
    await query.answer("📊 Загружаю…")

    user = await get_user(query.from_user.id)
    lang   = (user or {}).get("language", "ru")
    wallet = (user or {}).get("wallet_address", "")

    # ── Секция 1: Реальные позиции (если есть кошелёк) ────────────────
    real_positions = []
    if wallet:
        try:
            raw = await get_positions(query.from_user.id, wallet, force_refresh=False)
            real_positions = [enrich_position(p) for p in raw]
        except Exception as e:
            print(f"[Portfolio] Error getting positions: {e}")
            real_positions = []

    # ── Секция 2: Локальная статистика из БД ──────────────────────────
    stats   = await get_user_stats(query.from_user.id)
    bets    = await get_user_bets(query.from_user.id, limit=5)
    parlays = await get_user_parlays(query.from_user.id, limit=3)

    total_bets      = stats.get("total_bets", 0)
    total_invested  = stats.get("total_invested", 0.0)
    total_potential = stats.get("total_potential", 0.0)
    roi_potential   = ((total_potential - total_invested) / total_invested * 100) \
                      if total_invested > 0 else 0

    # ── Build portfolio text (clarity-first layout) ───────────────────
    ru = (lang == "ru")
    keyboard = []   # Инициализируем keyboard ДО цикла позиций (чтобы sell кнопки не затирались)

    if real_positions:
        open_pos   = [p for p in real_positions if not (p.get("resolved") or p.get("isResolved"))]
        closed_pos = [p for p in real_positions if p.get("resolved") or p.get("isResolved")]
        won   = sum(1 for p in closed_pos if p.get("pnl", 0) > 0)
        lost  = len(closed_pos) - won

        total_current = sum(p.get("current_value", 0) for p in open_pos)
        total_entry   = sum(p.get("entry_value",   0) for p in open_pos)
        total_pnl     = total_current - total_entry
        pnl_pct       = (total_pnl / total_entry * 100) if total_entry > 0 else 0
        pnl_emj       = "📈" if total_pnl >= 0 else "📉"
        pnl_sign      = "+" if total_pnl >= 0 else ""

        # ── Header ─────────────────────────────────────────────────────
        header_title = "📊 <b>Портфель</b>" if ru else "📊 <b>Portfolio</b>"
        lines = [header_title, ""]

        # Summary — current value first, then invested, then PnL
        if total_entry > 0:
            lines += [
                f"<b>${total_current:.2f}</b>  ←  ${total_entry:.2f} {'вложено' if ru else 'in'}",
                f"{pnl_emj} <b>{pnl_sign}${abs(total_pnl):.2f}</b>  ({pnl_sign}{abs(pnl_pct):.1f}%)",
                "",
            ]

        # Record — compact, no label clutter
        if closed_pos:
            lines.append(
                f"{'Открыто' if ru else 'Open'}  {len(open_pos)}   "
                f"{'Выиграно' if ru else 'Won'}  {won}   "
                f"{'Проиграно' if ru else 'Lost'}  {lost}"
            )
            lines.append("")

        # Open positions list — one line each, sorted by abs(pnl)
        # Сохраняем позиции в bot_data для sell flow
        if "sell_positions" not in ctx.bot_data:
            ctx.bot_data["sell_positions"] = {}

        if open_pos:
            lines.append("──────────────────")
            sorted_pos = sorted(open_pos, key=lambda x: abs(x.get("pnl", 0)), reverse=True)[:5]
            for i, p in enumerate(sorted_pos):
                # Кэшируем позицию для sell flow
                sell_idx = hash(str(query.from_user.id) + str(i)) % 100000
                ctx.bot_data["sell_positions"][sell_idx] = {
                    **p,
                    "user_id": query.from_user.id,
                }

                q   = (p.get("title") or p.get("question") or p.get("market", "?"))
                q   = q[:38] + "…" if len(q) > 38 else q
                out = p.get("outcome_label", "YES")
                cv  = p.get("current_value", 0)
                pnl = p.get("pnl", 0)
                pnl_disp = f"{'+' if pnl >= 0 else ''}{pnl:.2f}"
                color = "🟢" if pnl >= 0 else "🔴"
                lines.append(f"{color} {out}  ${cv:.2f}  {pnl_disp}   <i>{q}</i>")

                # Кнопка Продать для каждой позиции
                keyboard.append([
                    InlineKeyboardButton(
                        f"💰 {'Продать' if ru else 'Sell'}: {q[:25]}",
                        callback_data=f"sell:{sell_idx}"
                    )
                ])
            lines.append("──────────────────")
        elif not closed_pos:
            # Empty state — wallet connected, no positions
            lines.append("" )
            lines.append("— " + ("Открытых позиций нет" if ru else "No open positions"))
            lines.append("")
            lines.append("🧠 " + ("Intel Feed — найди первый сигнал" if ru
                                  else "Intel Feed — find your first trade"))

    else:
        # Fallback: local DB + live prices from Gamma API
        lines = [
            "📊 <b>Портфель</b>" if ru else "📊 <b>Portfolio</b>",
            "",
        ]
        if total_invested > 0 and bets:
            # Кэшируем позиции для sell flow
            if "sell_positions" not in ctx.bot_data:
                ctx.bot_data["sell_positions"] = {}

            # Подтягиваем live-цены для каждой ставки
            # Группируем по market_id чтобы не делать дублирующие запросы
            price_cache = {}  # market_id → {"YES": {"price": ..., "token_id": ...}, "NO": ...}
            for b in bets[:5]:
                mid = b.get("market_id", "")
                if not mid or mid in price_cache:
                    continue
                try:
                    # Strategy 1: condition_id (tries multiple methods internally)
                    prices = await gamma.get_prices_by_condition(mid)
                    if prices:
                        price_cache[mid] = prices
                        continue
                    # Strategy 2: по slug (если сохранён)
                    slug = b.get("slug", "")
                    if slug:
                        prices = await gamma.get_market_prices(slug)
                        if prices:
                            price_cache[mid] = prices
                            continue
                    print(f"[Portfolio] No live prices for {mid[:16]}...")
                except Exception as e:
                    print(f"[Portfolio] Failed to get live price for {mid[:12]}: {e}")

            # Считаем суммарный P&L
            total_current_val = 0.0
            total_entry_val = 0.0
            bet_details = []

            for i, b in enumerate(bets[:5]):
                o = b.get("outcome", "YES")
                a = float(b.get("amount", 0))
                p_price = float(b.get("price", 0.5))
                mid = b.get("market_id", "")
                size_shares = a / p_price if p_price > 0 else 0

                # Live цена из кэша
                live_price = p_price  # fallback = цена входа
                live_token_id = b.get("token_id", "")
                if mid in price_cache:
                    outcome_data = price_cache[mid].get(o.upper(), {})
                    if outcome_data.get("price"):
                        live_price = outcome_data["price"]
                    if outcome_data.get("token_id"):
                        live_token_id = outcome_data["token_id"]

                cur_val = size_shares * live_price
                entry_val = a
                pnl = cur_val - entry_val

                total_current_val += cur_val
                total_entry_val += entry_val

                bet_details.append({
                    "bet": b,
                    "outcome": o,
                    "amount": a,
                    "entry_price": p_price,
                    "live_price": live_price,
                    "size_shares": size_shares,
                    "cur_val": cur_val,
                    "entry_val": entry_val,
                    "pnl": pnl,
                    "token_id": live_token_id,
                    "market_id": mid,
                })

            total_pnl = total_current_val - total_entry_val
            pnl_pct = (total_pnl / total_entry_val * 100) if total_entry_val > 0 else 0
            pnl_emj = "📈" if total_pnl >= 0 else "📉"
            pnl_sign = "+" if total_pnl >= 0 else ""

            # Заголовок с суммарным P&L
            lines += [
                f"<b>${total_current_val:.2f}</b>  ←  ${total_entry_val:.2f} {'вложено' if ru else 'invested'}",
                f"{pnl_emj} <b>{pnl_sign}${abs(total_pnl):.2f}</b>  ({pnl_sign}{abs(pnl_pct):.1f}%)",
                "",
                f"{'Ставок' if ru else 'Trades'}  <b>{total_bets}</b>",
                "",
                "──────────────────",
            ]

            # Каждая ставка с live P&L
            for i, d in enumerate(bet_details):
                q = d["bet"].get("question", "—")
                q_display = q[:42] + "…" if len(q) > 42 else q
                o = d["outcome"]
                oe = "✅" if o == "YES" else "❌"
                pnl = d["pnl"]
                pnl_d = f"{'+' if pnl >= 0 else ''}{pnl:.2f}"
                color = "🟢" if pnl >= 0 else "🔴"

                # Позиция: вопрос + цены + P&L — в 2 строки
                price_changed = abs(d['live_price'] - d['entry_price']) > 0.001
                if price_changed:
                    price_str = f"${d['entry_price']:.2f} → <b>${d['live_price']:.2f}</b>"
                else:
                    price_str = f"${d['entry_price']:.2f}"

                lines.append(f"{color} {oe} <b>{o}</b>  {price_str}  <b>{pnl_d}</b>")
                lines.append(f"    <i>{q_display}</i>")

                # Кэшируем для sell
                sell_idx = hash(str(query.from_user.id) + "bet" + str(i)) % 100000
                ctx.bot_data["sell_positions"][sell_idx] = {
                    "user_id": query.from_user.id,
                    "title": q,
                    "question": q,
                    "outcome_label": o,
                    "outcome": o,
                    "side": o,
                    "size": d["size_shares"],
                    "size_tokens": round(d["size_shares"], 2),
                    "avgPrice": d["entry_price"],
                    "averagePrice": d["entry_price"],
                    "curPrice": d["live_price"],
                    "entry_value": d["entry_val"],
                    "current_value": d["cur_val"],
                    "pnl": d["pnl"],
                    "asset": d["token_id"],
                    "token_id": d["token_id"],
                    "market_id": d["market_id"],
                }

                # Кнопка Продать — короткая
                sell_val = f" ~${d['cur_val']:.2f}" if d["cur_val"] > 0.01 else ""
                keyboard.append([
                    InlineKeyboardButton(
                        f"💰 {'Продать' if ru else 'Sell'} #{i+1}{sell_val}",
                        callback_data=f"sell:{sell_idx}"
                    )
                ])

            lines.append("──────────────────")

        elif total_invested > 0:
            lines += [
                f"{'Ставок' if ru else 'Trades'}    <b>{total_bets}</b>",
                f"{'Вложено' if ru else 'Invested'}   <b>${total_invested:.2f}</b>",
                "",
            ]
        else:
            lines.append("— " + ("Сделок пока нет" if ru else "No trades yet"))
            lines.append("")
            lines.append("🔥 " + ("Горячие рынки → найди первую сделку" if ru
                                  else "Trending → find your first trade"))

    # Parlays (compact)
    if parlays:
        lines.append("")
        lines.append("🎯 " + ("Парлеи:" if ru else "Parlays:"))
        for p in parlays[:2]:
            n   = len(p.get("legs", []))
            amt = p.get("total_amount", 0)
            pot = p.get("potential_win", 0)
            odds_v = p.get("total_odds", 0)
            lines.append(f"   {n} legs  ${amt:.0f} → ${pot:.0f}  ({odds_v:.1f}x)")

    # ── Keyboard (навигация — добавляем к уже собранным sell-кнопкам) ──
    if wallet:
        keyboard.append([
            InlineKeyboardButton(
                "🔄 Обновить" if ru else "🔄 Refresh",
                callback_data="portfolio:refresh"
            ),
            InlineKeyboardButton(
                "📋 История" if ru else "📋 History",
                callback_data="portfolio:all"
            ),
        ])
    else:
        keyboard.append([
            InlineKeyboardButton(
                "📋 Сделки" if ru else "📋 Trades",
                callback_data="portfolio:all"
            ),
            InlineKeyboardButton(
                "🎯 Парлеи" if ru else "🎯 Parlays",
                callback_data="portfolio:parlays"
            ),
        ])

    keyboard.append([
        InlineKeyboardButton("🔥 Рынки" if ru else "🔥 Markets", callback_data="cat:trending"),
        InlineKeyboardButton("🔙 Меню" if ru else "🔙 Menu", callback_data="menu:main"),
    ])

    try:
        await query.edit_message_text(
            "\n".join(lines), parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        # edit_message_text не работает если предыдущее сообщение — фото (bet slip)
        # В этом случае отправляем новое сообщение
        print(f"[Portfolio] edit_message_text failed: {e}, sending new message")
        try:
            await query.message.reply_html(
                "\n".join(lines),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e2:
            print(f"[Portfolio] reply_html also failed: {e2}")


async def cb_portfolio_refresh(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Принудительное обновление позиций с Polymarket API."""
    query = update.callback_query
    await query.answer("🔄 Синхронизирую…")

    user   = await get_user(query.from_user.id)
    lang   = (user or {}).get("language", "ru")
    wallet = (user or {}).get("wallet_address", "")

    if not wallet:
        await query.answer("❌ Кошелёк не подключён" if lang=="ru" else "❌ No wallet", show_alert=True)
        return

    # Показываем индикатор загрузки
    loading = "🔄 <i>Синхронизирую позиции…</i>" if lang=="ru" else "🔄 <i>Syncing positions…</i>"
    await query.edit_message_text(loading, parse_mode="HTML")

    try:
        await get_positions(query.from_user.id, wallet, force_refresh=True)
    except Exception as e:
        err_msg = (
            f"⚠️ Не удалось обновить позиции\n<code>{str(e)[:60]}</code>"
            if lang == "ru" else
            f"⚠️ Failed to refresh positions\n<code>{str(e)[:60]}</code>"
        )
        keyboard = [[InlineKeyboardButton("🔙 Портфель" if lang=="ru" else "🔙 Portfolio",
                                           callback_data="portfolio")]]
        await query.edit_message_text(err_msg, parse_mode="HTML",
                                       reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # Перезагружаем экран портфеля с обновлёнными данными
    await cb_portfolio(update, ctx)


async def cb_portfolio_all(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Все сделки (до 20)."""
    query = update.callback_query
    await query.answer()

    user = await get_user(query.from_user.id)
    lang = (user or {}).get("language", "ru")
    bets = await get_user_bets(query.from_user.id, limit=20)

    header = "📋 <b>Все сделки</b>\n\n" if lang == "ru" else "📋 <b>All Trades</b>\n\n"

    if not bets:
        text = header + ("Сделок пока нет. Открой первую позицию!" if lang == "ru"
                        else "No trades yet. Open your first position!")
    else:
        lines = [header]
        for b in bets:
            q = b.get("question", "—")
            if len(q) > 40:
                q = q[:37] + "…"
            o = b.get("outcome", "")
            a = float(b.get("amount", 0))
            pw = float(b.get("potential_win", 0))
            pr = float(b.get("price", 0.5))
            date = b.get("created_at", "")[:10]
            oe = "✅" if o == "YES" else "❌"
            lines.append(f"{oe} <b>{o}</b> {pr:.0%} · ${a:.2f} → ${pw:.2f}")
            lines.append(f"   {q}  <i>({date})</i>")
            lines.append("")
        text = "\n".join(lines)

    keyboard = [[
        InlineKeyboardButton("🔙 Портфель" if lang=="ru" else "🔙 Portfolio",
                             callback_data="portfolio")
    ]]
    await query.edit_message_text(
        text, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def cb_watchlist(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Избранные рынки."""
    query = update.callback_query
    await query.answer()

    user   = await get_user(query.from_user.id)
    lang   = (user or {}).get("language", "ru")
    wl     = await get_watchlist(query.from_user.id)

    header = "⭐ <b>Избранное</b>\n\n" if lang == "ru" else "⭐ <b>Watchlist</b>\n\n"

    if not wl:
        text = header + ("Список пуст. Добавь рынки через кнопку ⭐"
                         if lang == "ru"
                         else "Empty. Add markets with the ⭐ button.")
    else:
        text = header
        for item in wl[:10]:
            q   = item.get("question", "—")
            if len(q) > 50:
                q = q[:47] + "…"
            text += f"• {q}\n"

    keyboard = [
        [InlineKeyboardButton(
            "📊 К рынкам" if lang == "ru" else "📊 Browse markets",
            callback_data="cat:markets"
        )],
        [InlineKeyboardButton(
            "🔙 Портфель" if lang == "ru" else "🔙 Portfolio",
            callback_data="portfolio"
        )],
    ]

    await query.edit_message_text(
        text, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ══════════════════════════════════════════════════════════════════════
# AI Handlers
# ══════════════════════════════════════════════════════════════════════

async def cb_ai_morning(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Утренний AI-брифинг."""
    query = update.callback_query
    await query.answer("🤖 Готовлю брифинг…")

    user = await get_user(query.from_user.id)
    lang = (user or {}).get("language", "ru")

    await query.edit_message_text(
        "🤖 <i>AI анализирует рынки… (~15 сек)</i>",
        parse_mode="HTML"
    )

    # Берём горячие спортивные рынки
    markets = await gamma.get_sports_markets(limit=5, tag="sports")
    if not markets:
        markets = await gamma.get_trending_markets(limit=5)

    # AI генерирует брифинг (async)
    briefing = await get_morning_briefing(markets, lang)

    header  = "🌅 <b>Утренний AI-брифинг</b>\n\n" if lang == "ru" \
              else "🌅 <b>Morning AI Briefing</b>\n\n"
    text    = header + briefing

    keyboard = [
        [InlineKeyboardButton("📊 К рынкам" if lang=="ru" else "📊 Browse markets",
                              callback_data="cat:markets"),
         InlineKeyboardButton("🎯 Парлей" if lang=="ru" else "🎯 Parlay",
                              callback_data="parlay:new")],
        [InlineKeyboardButton("🔙 Назад" if lang=="ru" else "🔙 Back",
                              callback_data="menu:main")],
    ]

    await query.edit_message_text(
        text, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def cmd_ai(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Команда /ai — утренний брифинг через команду."""
    user = await get_user(update.effective_user.id)
    lang = (user or {}).get("language", "ru")

    msg = await update.message.reply_html(
        "🤖 <i>Генерирую брифинг… (~15 сек)</i>"
    )

    markets  = await gamma.get_sports_markets(limit=5, tag="sports")
    briefing = await get_morning_briefing(markets, lang)

    header = "🌅 <b>Утренний AI-брифинг</b>\n\n" if lang == "ru" \
             else "🌅 <b>Morning AI Briefing</b>\n\n"

    await msg.edit_text(header + briefing, parse_mode="HTML")


async def cb_ai_market(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    Callback: ai:{idx} — AI-анализ рынка из кеша.
    Читаем рынок из ctx.bot_data["mc"] по числовому ключу.
    """
    query     = update.callback_query
    await query.answer("🤖 Анализирую…")

    # Парсим ai:{idx}
    idx = int(query.data.split(":")[1])
    market = ctx.bot_data.get("mc", {}).get(idx, {})

    user      = await get_user(query.from_user.id)
    lang      = (user or {}).get("language", "ru")

    if not market:
        await query.edit_message_text("❌ Рынок не найден. Обнови список.")
        return

    await query.edit_message_text(
        "🤖 <i>AI анализирует рынок… (~10 сек)</i>",
        parse_mode="HTML"
    )

    # AI генерирует прогноз (async)
    analysis = await get_sport_prediction(market, lang)

    question = market.get("question", market.get("title", "—"))
    header   = f"🤖 <b>AI Анализ</b>\n\n📌 {question}\n\n" if lang == "ru" \
               else f"🤖 <b>AI Analysis</b>\n\n📌 {question}\n\n"

    keyboard = [
        [InlineKeyboardButton("📊 К рынку" if lang == "ru" else "📊 Back to market",
                              callback_data=f"m:{idx}"),
         InlineKeyboardButton("🔍 Edge-анализ" if lang == "ru" else "🔍 Edge analysis",
                              callback_data=f"edge:{idx}")],
        [InlineKeyboardButton("🔙 Назад" if lang == "ru" else "🔙 Back",
                              callback_data="cat:markets")],
    ]

    await query.edit_message_text(
        header + analysis, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def cb_ai_edge(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Callback: edge:{idx} — анализ edge из кеша."""
    query   = update.callback_query
    await query.answer("🔍 Ищу edge…")

    idx = int(query.data.split(":")[1])
    market = ctx.bot_data.get("mc", {}).get(idx, {})

    user    = await get_user(query.from_user.id)
    lang    = (user or {}).get("language", "ru")

    if not market:
        await query.edit_message_text("❌ Рынок не найден. Обнови список.")
        return

    await query.edit_message_text("🔍 <i>Ищу edge… (~10 сек)</i>", parse_mode="HTML")

    analysis = await analyze_edge(market, lang)

    header = f"🔍 <b>Edge-анализ</b>\n\n" if lang == "ru" else f"🔍 <b>Edge Analysis</b>\n\n"

    keyboard = [
        [InlineKeyboardButton(
            "📊 К рынку" if lang == "ru" else "📊 Back",
            callback_data=f"m:{idx}"
        )],
        [InlineKeyboardButton("🔙 Назад" if lang == "ru" else "🔙 Back",
                              callback_data="cat:markets")],
    ]

    await query.edit_message_text(
        header + analysis, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
