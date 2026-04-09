# PolyScore — Handlers для ставок
# Buy YES/NO, подтверждение, bet slip карточка

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes, ConversationHandler
import io
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.polymarket import gamma, clob, relayer, format_volume, price_to_american_odds
from services.database import get_user, save_bet, create_user
from utils.bet_slip import create_bet_slip


# ══════════════════════════════════════════════════════════════════════
# States для ConversationHandler
# ══════════════════════════════════════════════════════════════════════
WAIT_AMOUNT = 1   # Ждём ввод суммы


async def cb_bet_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    Callback: b:Y:{idx} или b:N:{idx}
    Начало флоу ставки — запрашиваем сумму.
    Рынок берём из кеша ctx.bot_data["mc"].
    """
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")
    # b:Y:123 или b:N:123
    outcome = "YES" if parts[1] == "Y" else "NO"
    idx = int(parts[2])

    # ── WALLET GUARD (Fix #2) ─────────────────────────────────────────
    # Проверяем кошелёк ДО запроса суммы — не теряем время пользователя
    user = await get_user(query.from_user.id)
    lang = (user or {}).get("language", "ru")
    if not user or not user.get("wallet_address"):
        ctx.user_data["return_after_wallet"] = query.data  # вернёмся сюда после
        _msgs = {
            "ru": "💳 <b>Нужен кошелёк для торговли</b>\n\nСоздай Polygon кошелёк за 5 секунд или подключи существующий. Сделка тебя подождёт 🕐",
            "en": "💳 <b>Wallet required to trade</b>\n\nCreate a Polygon wallet in 5 seconds or connect an existing one. Your trade will wait 🕐",
            "es": "💳 <b>Se necesita cartera para operar</b>\n\nCrea una cartera Polygon en 5 segundos o conecta una existente. Tu operación te espera 🕐",
            "pt": "💳 <b>Carteira necessária para operar</b>\n\nCrie uma carteira Polygon em 5 segundos ou conecte uma existente. Seu trade vai esperar 🕐",
        }
        _create = {"ru": "🚀 Создать кошелёк", "en": "🚀 Create Wallet", "es": "🚀 Crear cartera", "pt": "🚀 Criar carteira"}
        _add    = {"ru": "📲 Уже есть кошелёк", "en": "📲 I have a wallet", "es": "📲 Ya tengo cartera", "pt": "📲 Já tenho carteira"}
        _back   = {"ru": "🔙 Назад", "en": "🔙 Back", "es": "🔙 Atrás", "pt": "🔙 Voltar"}
        _l = lang if lang in _msgs else "en"
        await query.edit_message_text(
            _msgs[_l], parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(_create.get(_l, _create["en"]), callback_data="wallet:create")],
                [InlineKeyboardButton(_add.get(_l, _add["en"]),       callback_data="wallet:add")],
                [InlineKeyboardButton(_back.get(_l, _back["en"]),     callback_data="cat:markets")],
            ])
        )
        return ConversationHandler.END
    # ─────────────────────────────────────────────────────────────────

    # Получаем рынок из кеша (Fix #3: graceful fallback)
    market = ctx.bot_data.get("mc", {}).get(idx, {})
    if not market:
        _no_mkt = {"ru": "❌ Список рынков обновился. Открой категорию снова.", "en": "❌ Market list refreshed. Please browse again."}
        await query.edit_message_text(
            _no_mkt.get(lang, _no_mkt["en"]),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📊 Рынки" if lang == "ru" else "📊 Markets", callback_data="cat:markets")
            ]])
        )
        return ConversationHandler.END

    # Извлекаем данные рынка
    cond_id  = market.get("conditionId") or market.get("condition_id", "")
    slug     = market.get("slug", "")
    question = market.get("question") or market.get("title", cond_id)
    yes_p, no_p = gamma.extract_prices(market)
    price = yes_p if outcome == "YES" else no_p
    if price <= 0:
        price = 0.5  # fallback

    # ── REAL TOKEN ID — resolve YES/NO CLOB token from market ────────
    # /events endpoint returns clobTokenIds: JSON array ["tokenYES","tokenNO"]
    # tokens[] is always empty in /events responses — cannot be used.
    # Convention: index 0 = YES, index 1 = NO (Polymarket standard).
    yes_token_id = ""
    no_token_id  = ""

    # Path 1: clobTokenIds (present on all /events markets, always populated)
    clob_ids_raw = market.get("clobTokenIds")
    if clob_ids_raw:
        try:
            import json as _j
            ids = _j.loads(clob_ids_raw) if isinstance(clob_ids_raw, str) else clob_ids_raw
            if len(ids) >= 2:
                yes_token_id = ids[0]
                no_token_id  = ids[1]
        except Exception:
            pass

    # Path 2: tokens[] fallback (present on /markets endpoint responses)
    if not yes_token_id:
        tokens = market.get("tokens", [])
        for t in tokens:
            outcome_str = t.get("outcome", "").upper()
            if outcome_str == "YES":
                yes_token_id = t.get("token_id", "")
            elif outcome_str == "NO":
                no_token_id = t.get("token_id", "")

    # Path 3: fetch from Gamma API by slug (last resort — one HTTP call)
    if not yes_token_id:
        try:
            prices = await gamma.get_market_prices(slug or cond_id)
            if prices:
                yes_token_id = (prices.get("YES") or {}).get("token_id", "")
                no_token_id  = (prices.get("NO")  or {}).get("token_id", "")
        except Exception:
            pass

    real_token_id = yes_token_id if outcome == "YES" else no_token_id
    # ─────────────────────────────────────────────────────────────────

    # Сохраняем в ctx.user_data для продолжения флоу
    ctx.user_data["bet"] = {
        "outcome":    outcome,
        "cond_id":    cond_id,
        "slug":       slug,
        "question":   question,
        "token_id":   real_token_id,  # real CLOB token ID (YES or NO)
        "price":      price,
        "lang":       lang,
        "message_id": query.message.message_id,
        "chat_id":    query.message.chat_id,
    }

    odds  = price_to_american_odds(price)
    prob  = f"{price:.0%}"
    outcome_emoji = "✅" if outcome == "YES" else "❌"

    # ── Friction reducer: if amount pre-filled (from Intel), skip to confirm
    prefill = ctx.user_data.pop("prefill_amount", None)
    signal_src = ctx.user_data.pop("signal_source", None)
    if prefill and prefill >= 1:
        amount = float(prefill)
        ctx.user_data["bet"]["amount"] = amount
        potential = amount / price if price > 0 else 0
        profit    = potential - amount

        q_short = question[:55] + "…" if len(question) > 55 else question

        if lang == "ru":
            text = (
                f"{outcome_emoji} <b>{outcome}</b>  ·  ${amount:.2f}\n"
                f"\n"
                f"<i>{q_short}</i>\n"
                f"\n"
                f"Вход <b>{prob}</b>  →  выигрыш <b>${potential:.2f}</b>  (+${profit:.2f})"
            )
            btn_confirm = f"✅ Купить за ${amount:.0f}"
            btn_cancel  = "❌ Отмена"
        else:
            text = (
                f"{outcome_emoji} <b>{outcome}</b>  ·  ${amount:.2f}\n"
                f"\n"
                f"<i>{q_short}</i>\n"
                f"\n"
                f"Buy at <b>{prob}</b>  →  win <b>${potential:.2f}</b>  (+${profit:.2f})"
            )
            btn_confirm = f"✅ Confirm ${amount:.0f}"
            btn_cancel  = "❌ Cancel"

        keyboard = [[
            InlineKeyboardButton(btn_confirm, callback_data="bet:confirm"),
            InlineKeyboardButton(btn_cancel,  callback_data="bet:cancel"),
        ]]
        await query.edit_message_text(text, parse_mode="HTML",
                                       reply_markup=InlineKeyboardMarkup(keyboard))
        return ConversationHandler.END
    # ─────────────────────────────────────────────────────────────────

    # No prefill — ask for amount
    q_short = question[:55] + "…" if len(question) > 55 else question
    if lang == "ru":
        text = (
            f"{outcome_emoji} <b>{outcome}</b>  ·  {prob} за акцию\n"
            f"\n"
            f"<i>{q_short}</i>\n"
            f"\n"
            f"Сколько вложить?"
        )
    else:
        text = (
            f"{outcome_emoji} <b>{outcome}</b>  ·  {prob} per share\n"
            f"\n"
            f"<i>{q_short}</i>\n"
            f"\n"
            f"How much?"
        )

    # Quick-amount buttons for speed
    keyboard = [
        [
            InlineKeyboardButton("$10",  callback_data="bet:quick:10"),
            InlineKeyboardButton("$25",  callback_data="bet:quick:25"),
            InlineKeyboardButton("$50",  callback_data="bet:quick:50"),
        ],
        [InlineKeyboardButton(
            "❌ Отмена" if lang == "ru" else "❌ Cancel",
            callback_data="bet:cancel"
        )],
    ]

    await query.edit_message_text(
        text, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return WAIT_AMOUNT


def _build_confirm_text(bet: dict, amount: float, lang: str) -> tuple[str, list]:
    """
    Build confirm-screen text + keyboard.
    Used by both msg_bet_amount and cb_bet_quick.
    Short and clear — user sees exactly what they get.
    """
    outcome       = bet.get("outcome", "YES")
    price         = bet.get("price", 0.5)
    question      = bet.get("question", "")
    potential     = amount / price if price > 0 else 0
    profit        = potential - amount
    outcome_emoji = "✅" if outcome == "YES" else "❌"
    q_short       = question[:55] + "…" if len(question) > 55 else question

    if lang == "ru":
        text = (
            f"{outcome_emoji} <b>{outcome}</b>  ·  ${amount:.2f}\n"
            f"\n"
            f"<i>{q_short}</i>\n"
            f"\n"
            f"Вход <b>{price:.0%}</b>  →  выигрыш <b>${potential:.2f}</b>  (+${profit:.2f})"
        )
        btn_ok  = f"✅ Купить за ${amount:.0f}"
        btn_no  = "❌ Отмена"
    else:
        text = (
            f"{outcome_emoji} <b>{outcome}</b>  ·  ${amount:.2f}\n"
            f"\n"
            f"<i>{q_short}</i>\n"
            f"\n"
            f"Buy at <b>{price:.0%}</b>  →  win <b>${potential:.2f}</b>  (+${profit:.2f})"
        )
        btn_ok = f"✅ Confirm ${amount:.0f}"
        btn_no = "❌ Cancel"

    keyboard = [[
        InlineKeyboardButton(btn_ok, callback_data="bet:confirm"),
        InlineKeyboardButton(btn_no, callback_data="bet:cancel"),
    ]]
    return text, keyboard


async def msg_bet_amount(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    User typed an amount. Show confirm screen.
    """
    bet  = ctx.user_data.get("bet", {})
    lang = bet.get("lang", "ru")

    try:
        amount = float(update.message.text.strip().replace(",", "."))
    except ValueError:
        err = "❌ Введи число: 10 или 25" if lang == "ru" else "❌ Enter a number: e.g. 10"
        await update.message.reply_text(err)
        return WAIT_AMOUNT

    if amount < 1:
        err = "❌ Минимум $1 USDC" if lang == "ru" else "❌ Minimum $1 USDC"
        await update.message.reply_text(err)
        return WAIT_AMOUNT

    bet["amount"] = amount
    ctx.user_data["bet"] = bet

    text, keyboard = _build_confirm_text(bet, amount, lang)
    await update.message.reply_html(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END


async def cb_bet_quick(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    Callback: bet:quick:{amount} — user tapped a quick-amount button.
    Skips text input entirely → straight to confirm. (Tap → Confirm → Done)
    """
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")
    try:
        amount = float(parts[2])
    except (IndexError, ValueError):
        await query.answer("Invalid amount", show_alert=True)
        return

    bet = ctx.user_data.get("bet", {})
    if not bet:
        await query.edit_message_text("❌ Session expired. Start again.")
        return

    lang = bet.get("lang", "ru")
    bet["amount"] = amount
    ctx.user_data["bet"] = bet

    text, keyboard = _build_confirm_text(bet, amount, lang)
    await query.edit_message_text(text, parse_mode="HTML",
                                   reply_markup=InlineKeyboardMarkup(keyboard))


async def cb_bet_confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    Callback: bet:confirm — исполнить ставку.
    """
    query = update.callback_query
    await query.answer()

    bet      = ctx.user_data.get("bet", {})
    user_tg  = query.from_user
    user_db  = await get_user(user_tg.id)
    lang     = bet.get("lang", "ru")

    if not bet:
        await query.edit_message_text("❌ Сессия сделки истекла. Начни заново.")
        return

    outcome  = bet.get("outcome", "YES")
    price    = bet.get("price", 0.5)
    amount   = bet.get("amount", 0)
    cond_id  = bet.get("cond_id", "")
    token_id = bet.get("token_id", "")

    # Вопрос берём из user_data (сохранён при cb_bet_start)
    question = bet.get("question", cond_id)

    # ── Safety guards ─────────────────────────────────────────────────
    if not amount or amount <= 0:
        await query.edit_message_text("❌ Некорректная сумма. Начни заново." if lang == "ru" else "❌ Invalid amount. Please start over.")
        return
    if price <= 0 or price >= 1:
        await query.edit_message_text("❌ Некорректная цена рынка. Рынок мог закрыться." if lang == "ru" else "❌ Invalid market price. The market may have closed.")
        return
    from config import POLY_API_KEY, POLY_SECRET, POLY_PASSPHRASE
    if POLY_API_KEY and not token_id:
        await query.edit_message_text("❌ Не удалось получить ID токена рынка. Попробуй снова." if lang == "ru" else "❌ Could not resolve market token ID. Please try again.")
        return
    # ── End safety guards ─────────────────────────────────────────────

    # ──────────────────────────────────────────────────────────────────
    # EXECUTION — Real CLOB if keys present, explicit Demo otherwise
    # ──────────────────────────────────────────────────────────────────
    import os
    from config import POLY_API_KEY, POLY_SECRET, POLY_PASSPHRASE, BUILDER_CODE

    order_id  = ""
    is_demo   = False
    exec_error = ""

    production_keys_set = bool(POLY_API_KEY and POLY_SECRET and POLY_PASSPHRASE)

    if production_keys_set and token_id:
        # ── REAL execution path ───────────────────────────────────────

        # Step 0: wallet обязателен для реальных сделок
        wallet_address = (user_db or {}).get("wallet_address", "")
        if not wallet_address:
            _no_wallet = {
                "ru": "❌ <b>Кошелёк не подключён</b>\n\nПодключи кошелёк через /wallet и попробуй снова.",
                "en": "❌ <b>Wallet not connected</b>\n\nConnect your wallet via /wallet and try again.",
            }
            await query.edit_message_text(
                _no_wallet.get(lang, _no_wallet["en"]), parse_mode="HTML"
            )
            return

        # Step 1: проверка баланса — ОТДЕЛЬНЫМ aiohttp запросом
        import aiohttp as _aiohttp
        balance = 0.0
        balance_ok = False
        print(f"[Balance] START wallet={wallet_address}")
        try:
            usdc_native = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
            usdc_bridged = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
            addr_padded = wallet_address[2:].lower()
            call_data = f"0x70a08231000000000000000000000000{addr_padded}"
            print(f"[Balance] call_data={call_data}")

            _timeout = _aiohttp.ClientTimeout(total=15)
            async with _aiohttp.ClientSession(timeout=_timeout) as _s:
                for cname, contract in [("native", usdc_native), ("bridged", usdc_bridged)]:
                    found = False
                    for rpc in [
                        "https://polygon-bor-rpc.publicnode.com",
                        "https://polygon.drpc.org",
                        "https://1rpc.io/matic",
                    ]:
                        try:
                            payload = {
                                "jsonrpc": "2.0",
                                "method": "eth_call",
                                "params": [{"to": contract, "data": call_data}, "latest"],
                                "id": 1,
                            }
                            print(f"[Balance] Trying {cname} via {rpc}...")
                            async with _s.post(rpc, json=payload,
                                               headers={"Content-Type": "application/json"}) as _r:
                                print(f"[Balance]   status={_r.status}")
                                body = await _r.text()
                                print(f"[Balance]   body={body[:200]}")
                                if _r.status == 200:
                                    import json as _json
                                    _res = _json.loads(body)
                                    _hex = _res.get("result", "0x0") or "0x0"
                                    print(f"[Balance]   hex={_hex}")
                                    raw = int(_hex, 16)
                                    usdc_val = raw / 1_000_000
                                    print(f"[Balance]   raw={raw} usdc=${usdc_val:.6f}")
                                    balance += usdc_val
                                    balance_ok = True
                                    found = True
                                    break
                        except Exception as _e:
                            print(f"[Balance]   EXCEPTION: {type(_e).__name__}: {_e}")
                            continue
                    if not found:
                        print(f"[Balance]   {cname}: all RPCs failed")

            print(f"[Balance] RESULT: ${balance:.6f} ok={balance_ok}")
        except Exception as _e:
            print(f"[Balance] TOTAL FAILURE: {type(_e).__name__}: {_e}")

        if balance_ok and balance < amount:
            _insuf = {
                "ru": f"❌ <b>Недостаточно USDC</b>\n\nНа кошельке: <b>${balance:.2f}</b>\nНужно: <b>${amount:.2f}</b>\n\nПополни кошелёк и попробуй снова.",
                "en": f"❌ <b>Insufficient USDC</b>\n\nWallet balance: <b>${balance:.2f}</b>\nRequired: <b>${amount:.2f}</b>\n\nFund your wallet and try again.",
            }
            await query.edit_message_text(
                _insuf.get(lang, _insuf["en"]), parse_mode="HTML"
            )
            return

        # Step 2: размещение ордера через py-clob-client
        # ВАЖНО: используем create_order (limit order) вместо create_market_order,
        # потому что create_market_order делит amount/price → бесконечные дроби →
        # сервер отклоняет "invalid amounts, max accuracy of N decimals".
        # create_order принимает size (shares) и price, считает maker = size * price
        # (умножение вместо деления) — decimal precision всегда корректна.
        try:
            from py_clob_client.client import ClobClient as PyClob
            from py_clob_client.clob_types import OrderArgs, OrderType, ApiCreds
            from py_builder_signing_sdk.config import BuilderConfig
            from py_builder_signing_sdk.sdk_types import BuilderApiKeyCreds

            poly_private_key = os.getenv("POLY_PRIVATE_KEY", "")
            if not poly_private_key:
                exec_error = "POLY_PRIVATE_KEY not set — cannot sign order"
            else:
                # Builder attribution для builder rewards
                _bc = None
                _bk = os.getenv("BUILDER_API_KEY", "")
                _bs = os.getenv("BUILDER_SECRET", "")
                _bp = os.getenv("BUILDER_PASSPHRASE", "")
                if all([_bk, _bs, _bp]):
                    _bc = BuilderConfig(local_builder_creds=BuilderApiKeyCreds(key=_bk, secret=_bs, passphrase=_bp))

                py_clob = PyClob(
                    host="https://clob.polymarket.com",
                    key=poly_private_key,
                    chain_id=137,
                    builder_config=_bc,
                )
                py_clob.set_api_creds(ApiCreds(
                    api_key=POLY_API_KEY,
                    api_secret=POLY_SECRET,
                    api_passphrase=POLY_PASSPHRASE,
                ))

                # OrderArgs для limit order:
                #   size  = количество акций (shares) — max 2 decimals
                #   price = цена за акцию — decimals зависят от tick_size рынка
                # amount (в долларах) → size (акции): size = amount / price
                # Округляем size вниз до 2 decimals (CLOB требование)
                from math import floor, ceil
                price_f = float(price)
                amount_f = float(amount)

                # Получаем min_order_size из orderbook рынка
                min_size = 5.0  # дефолт на случай если не удастся получить
                try:
                    book = py_clob.get_order_book(token_id)
                    if book and hasattr(book, 'min_order_size') and book.min_order_size:
                        min_size = float(book.min_order_size)
                        print(f"[Order] min_order_size from orderbook: {min_size}")
                except Exception as e:
                    print(f"[Order] Could not get min_order_size: {e}, using default {min_size}")

                size_raw = amount_f / price_f
                size_rounded = floor(size_raw * 100) / 100  # round DOWN to 2 decimals

                # Если size меньше минимума — поднимаем до минимума
                if size_rounded < min_size:
                    size_rounded = min_size
                    # Пересчитываем реальную стоимость
                    real_cost = size_rounded * price_f
                    print(f"[Order] Size bumped to minimum: {size_rounded} shares, cost=${real_cost:.2f}")
                    # Проверяем хватает ли баланса
                    if balance_ok and real_cost > balance:
                        _min_msg = {
                            "ru": f"❌ <b>Минимальный ордер</b>\n\nНа этом рынке минимум <b>{min_size:.0f} шт.</b> = <b>${real_cost:.2f}</b>\nВаш баланс: <b>${balance:.2f}</b>\n\nПополните кошелёк или выберите другой рынок.",
                            "en": f"❌ <b>Minimum order size</b>\n\nThis market requires at least <b>{min_size:.0f} shares</b> = <b>${real_cost:.2f}</b>\nYour balance: <b>${balance:.2f}</b>\n\nFund your wallet or choose a different market.",
                        }
                        await query.edit_message_text(
                            _min_msg.get(lang, _min_msg["en"]), parse_mode="HTML"
                        )
                        return

                if size_rounded < 0.01:
                    exec_error = f"Order too small: ${amount_f} at {price_f} = {size_raw:.4f} shares (min 0.01)"
                else:
                    order_args = OrderArgs(
                        token_id=token_id,
                        size=size_rounded,
                        side="BUY",
                        price=price_f,
                    )
                    real_cost = size_rounded * price_f
                    print(f"[Order] Placing LIMIT: token={token_id[:16]}... size={size_rounded} shares, price={price_f}, cost=${real_cost:.2f}")

                    signed_order = py_clob.create_order(order_args)
                    resp = py_clob.post_order(signed_order, OrderType.GTC)
                    print(f"[Order] CLOB response: {resp}")

                    if resp and resp.get("orderID"):
                        order_id = resp["orderID"]
                    elif resp and resp.get("success") is False:
                        exec_error = resp.get("errorMsg", "CLOB rejected the order")
                    elif resp and resp.get("errorMsg"):
                        exec_error = resp["errorMsg"]
                    else:
                        exec_error = f"Unexpected CLOB response: {resp}"

        except ImportError:
            exec_error = "py-clob-client not installed — run: pip install py-clob-client"
        except Exception as e:
            exec_error = str(e)
            print(f"[Order] Exception: {exec_error}")

        if exec_error:
            _fail = {
                "ru": f"❌ <b>Ордер не размещён</b>\n\n<i>{exec_error}</i>\n\nПроверь баланс и попробуй снова или обратись в @PolyScoreSupport",
                "en": f"❌ <b>Order not placed</b>\n\n<i>{exec_error}</i>\n\nCheck your balance and try again, or contact @PolyScoreSupport",
            }
            await query.edit_message_text(
                _fail.get(lang, _fail["en"]), parse_mode="HTML"
            )
            return

    else:
        # ── DEMO mode — keys not configured ──────────────────────────
        is_demo = True
        order_id = f"demo_{int(query.message.date.timestamp())}"

    # If we got here with no order_id and no error, something is wrong
    if not order_id:
        order_id = f"demo_{int(query.message.date.timestamp())}"
        is_demo = True
    # ──────────────────────────────────────────────────────────────────

    slug = bet.get("slug", "")
    bet_id = await save_bet(
        user_id   = user_tg.id,
        market_id = cond_id,
        question  = question,
        outcome   = outcome,
        amount    = amount,
        price     = price,
        order_id  = order_id,
        token_id  = token_id,
        slug      = slug,
    )

    potential  = amount / price if price > 0 else 0
    odds       = price_to_american_odds(price)

    # Генерируем bet slip карточку
    username = user_tg.username or str(user_tg.id)
    slip_img = create_bet_slip(
        question  = question,
        outcome   = outcome,
        amount    = amount,
        price     = price,
        market_id = cond_id,
        username  = username,
    )

    outcome_emoji = "✅" if outcome == "YES" else "❌"
    q_short = question[:55] + "…" if len(question) > 55 else question
    # is_demo already set in execution block above

    if lang == "ru":
        if is_demo:
            mode_note = "\n\n⚠️ <i>Demo режим — реальные деньги не задействованы</i>"
        else:
            mode_note = f"\n\n🔑 <i>Order ID: {order_id[:16]}…</i>"
        caption = (
            f"{'⚠️ DEMO' if is_demo else '✅'} <b>{'Сделка (demo)' if is_demo else 'Сделка открыта'}</b>\n\n"
            f"{outcome_emoji} <b>{outcome}</b>  ·  ${amount:.2f}\n\n"
            f"<i>{q_short}</i>\n\n"
            f"Вход <b>{price:.0%}</b>  →  потенциал <b>${potential:.2f}</b>  (+${potential - amount:.2f})"
            f"{mode_note}"
        )
    else:
        if is_demo:
            mode_note = "\n\n⚠️ <i>Demo mode — no real money involved</i>"
        else:
            mode_note = f"\n\n🔑 <i>Order ID: {order_id[:16]}…</i>"
        caption = (
            f"{'⚠️ DEMO' if is_demo else '✅'} <b>{'Trade (demo)' if is_demo else 'Trade opened'}</b>\n\n"
            f"{outcome_emoji} <b>{outcome}</b>  ·  ${amount:.2f}\n\n"
            f"<i>{q_short}</i>\n\n"
            f"Entry <b>{price:.0%}</b>  →  win <b>${potential:.2f}</b>  (+${potential - amount:.2f})"
            f"{mode_note}"
        )

    keyboard = [[
        InlineKeyboardButton("📊 Портфель" if lang=="ru" else "📊 Portfolio",
                             callback_data="portfolio"),
        InlineKeyboardButton("🔥 Рынки" if lang=="ru" else "🔥 Markets",
                             callback_data="cat:trending"),
    ]]

    # Отправляем bet slip как фото
    await query.message.reply_photo(
        photo=io.BytesIO(slip_img),
        caption=caption,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await query.edit_message_text("✅ Сделка размещена!")


async def cb_bet_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Callback: bet:cancel — отмена."""
    query = update.callback_query
    await query.answer()
    user = await get_user(query.from_user.id)
    lang = (user or {}).get("language", "ru")
    msg  = "❌ Сделка отменена." if lang == "ru" else "❌ Trade cancelled."
    await query.edit_message_text(msg)
    ctx.user_data.pop("bet", None)
    return ConversationHandler.END


# ══════════════════════════════════════════════════════════════════════
# SELL FLOW — продажа позиции
# ══════════════════════════════════════════════════════════════════════

async def cb_sell_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    Callback: sell:{idx} — начало продажи позиции.
    Показывает экран подтверждения: что продаём, текущая цена, P&L.
    """
    query = update.callback_query
    await query.answer("💰 Загружаю…")

    user = await get_user(query.from_user.id)
    lang = (user or {}).get("language", "ru")

    # Получаем позицию из кэша
    sell_idx = int(query.data.split(":")[1])
    pos = ctx.bot_data.get("sell_positions", {}).get(sell_idx)

    if not pos or pos.get("user_id") != query.from_user.id:
        msg = "❌ Позиция не найдена. Обнови портфель." if lang == "ru" \
              else "❌ Position not found. Refresh portfolio."
        await query.edit_message_text(msg)
        return

    # Извлекаем данные позиции
    question   = pos.get("title") or pos.get("question") or pos.get("market", "?")
    outcome    = pos.get("outcome_label") or pos.get("outcome") or pos.get("side", "YES")
    size       = float(pos.get("size_tokens") or pos.get("size") or 0)
    cur_price  = float(pos.get("curPrice") or pos.get("currentPrice") or pos.get("avgPrice") or 0)
    avg_price  = float(pos.get("avgPrice") or pos.get("averagePrice") or 0)
    entry_val  = float(pos.get("entry_value", 0))
    cur_val    = float(pos.get("current_value", 0))
    pnl        = float(pos.get("pnl", 0))

    # token_id для CLOB — ищем в разных полях
    token_id = (pos.get("asset") or pos.get("token_id") or
                pos.get("tokenId") or pos.get("assetId") or "")

    # Fallback: resolve token_id по market_id (conditionId) + outcome через Gamma API
    if not token_id and pos.get("market_id"):
        try:
            market_info = await gamma.get_market_prices(pos["market_id"])
            if market_info:
                outcome_key = outcome.upper()
                token_data = market_info.get(outcome_key, {})
                token_id = token_data.get("token_id", "")
                if token_id:
                    print(f"[Sell] Resolved token_id from Gamma: {token_id[:16]}...")
        except Exception as e:
            print(f"[Sell] Failed to resolve token_id from Gamma: {e}")

    if not token_id:
        msg = "❌ Не удалось определить токен позиции. Попробуй продать на polymarket.com" \
              if lang == "ru" \
              else "❌ Could not resolve position token. Try selling on polymarket.com"
        try:
            await query.edit_message_text(msg)
        except Exception:
            await query.message.reply_text(msg)
        return

    # Сохраняем данные для подтверждения
    user_db = await get_user(query.from_user.id)
    wallet_address = (user_db or {}).get("wallet_address", "")
    ctx.user_data["sell"] = {
        "sell_idx":       sell_idx,
        "token_id":       token_id,
        "outcome":        outcome,
        "question":       question,
        "size":           size,
        "cur_price":      cur_price,
        "avg_price":      avg_price,
        "entry_val":      entry_val,
        "cur_val":        cur_val,
        "pnl":            pnl,
        "lang":           lang,
        "wallet_address": wallet_address,
    }

    q_short = question[:55] + "…" if len(question) > 55 else question
    outcome_emoji = "✅" if outcome.upper() == "YES" else "❌"
    pnl_sign = "+" if pnl >= 0 else ""
    pnl_emoji = "📈" if pnl >= 0 else "📉"

    if lang == "ru":
        text = (
            f"💰 <b>Продать позицию</b>\n\n"
            f"{outcome_emoji} <b>{outcome}</b>  ·  {size:.2f} шт.\n\n"
            f"<i>{q_short}</i>\n\n"
            f"Вход: <b>${avg_price:.2f}</b>  →  Сейчас: <b>${cur_price:.2f}</b>\n"
            f"Стоимость: <b>${cur_val:.2f}</b>\n"
            f"{pnl_emoji} P&L: <b>{pnl_sign}${abs(pnl):.2f}</b>\n\n"
            f"Продать <b>все {size:.2f} шт.</b> по рыночной цене?"
        )
        btn_sell = f"💰 Продать за ~${cur_val:.2f}"
        btn_cancel = "❌ Отмена"
    else:
        text = (
            f"💰 <b>Sell Position</b>\n\n"
            f"{outcome_emoji} <b>{outcome}</b>  ·  {size:.2f} shares\n\n"
            f"<i>{q_short}</i>\n\n"
            f"Entry: <b>${avg_price:.2f}</b>  →  Now: <b>${cur_price:.2f}</b>\n"
            f"Value: <b>${cur_val:.2f}</b>\n"
            f"{pnl_emoji} P&L: <b>{pnl_sign}${abs(pnl):.2f}</b>\n\n"
            f"Sell <b>all {size:.2f} shares</b> at market price?"
        )
        btn_sell = f"💰 Sell for ~${cur_val:.2f}"
        btn_cancel = "❌ Cancel"

    keyboard = [[
        InlineKeyboardButton(btn_sell, callback_data="sell:confirm"),
        InlineKeyboardButton(btn_cancel, callback_data="sell:cancel"),
    ]]

    try:
        await query.edit_message_text(text, parse_mode="HTML",
                                       reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception:
        await query.message.reply_html(text,
                                        reply_markup=InlineKeyboardMarkup(keyboard))


async def cb_sell_confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    Callback: sell:confirm — исполнить продажу через CLOB.
    Используем create_order с side="SELL".
    """
    query = update.callback_query
    await query.answer("💰 Размещаю ордер…")

    sell = ctx.user_data.get("sell", {})
    lang = sell.get("lang", "ru")

    if not sell:
        await query.edit_message_text(
            "❌ Сессия продажи истекла. Открой портфель заново." if lang == "ru"
            else "❌ Sell session expired. Open portfolio again."
        )
        return

    token_id  = sell["token_id"]
    size      = sell["size"]
    cur_price = sell["cur_price"]
    question  = sell["question"]
    outcome   = sell["outcome"]

    # Показываем индикатор
    loading = "💰 <i>Размещаю ордер на продажу…</i>" if lang == "ru" \
              else "💰 <i>Placing sell order…</i>"
    try:
        await query.edit_message_text(loading, parse_mode="HTML")
    except Exception:
        pass

    # ── SELL через py-clob-client ──────────────────────────────────────
    import os
    from config import POLY_API_KEY, POLY_SECRET, POLY_PASSPHRASE

    exec_error = ""
    order_id = ""

    if not (POLY_API_KEY and POLY_SECRET and POLY_PASSPHRASE):
        exec_error = "API keys not configured"
    else:
        try:
            from py_clob_client.client import ClobClient as PyClob
            from py_clob_client.clob_types import OrderArgs, OrderType, ApiCreds
            from py_builder_signing_sdk.config import BuilderConfig
            from py_builder_signing_sdk.sdk_types import BuilderApiKeyCreds
            from math import floor

            poly_private_key = os.getenv("POLY_PRIVATE_KEY", "")
            if not poly_private_key:
                exec_error = "POLY_PRIVATE_KEY not set"
            else:
                # Builder attribution для builder rewards
                _bc = None
                _bk = os.getenv("BUILDER_API_KEY", "")
                _bs = os.getenv("BUILDER_SECRET", "")
                _bp = os.getenv("BUILDER_PASSPHRASE", "")
                if all([_bk, _bs, _bp]):
                    _bc = BuilderConfig(local_builder_creds=BuilderApiKeyCreds(key=_bk, secret=_bs, passphrase=_bp))

                py_clob = PyClob(
                    host="https://clob.polymarket.com",
                    key=poly_private_key,
                    chain_id=137,
                    builder_config=_bc,
                )
                py_clob.set_api_creds(ApiCreds(
                    api_key=POLY_API_KEY,
                    api_secret=POLY_SECRET,
                    api_passphrase=POLY_PASSPHRASE,
                ))

                # Для SELL: size = кол-во акций, price = текущая цена
                # Округляем size вниз до 2 decimals (CLOB требование)
                size_rounded = floor(size * 100) / 100

                if size_rounded < 0.01:
                    exec_error = f"Position too small to sell: {size:.4f} shares"
                else:
                    # Market sell: ставим цену ниже рыночной для мгновенного исполнения
                    # Снижаем на 5% от текущей цены, минимум 0.01
                    raw_price = float(cur_price)
                    market_price = max(round(raw_price * 0.95, 2), 0.01)
                    # CLOB price: от 0.01 до 0.99, шаг 0.01
                    price_f = min(max(market_price, 0.01), 0.99)
                    print(f"[Sell] Market sell: raw_price={raw_price}, sell_price={price_f}")

                    # Получаем min_order_size
                    min_size = 5.0
                    try:
                        book = py_clob.get_order_book(token_id)
                        if book and hasattr(book, 'min_order_size') and book.min_order_size:
                            min_size = float(book.min_order_size)
                            print(f"[Sell] min_order_size: {min_size}")
                        # Если есть best bid — используем его для ещё более точной цены
                        if book and hasattr(book, 'bids') and book.bids:
                            best_bid = float(book.bids[0].price) if book.bids else None
                            if best_bid and best_bid > 0:
                                price_f = best_bid
                                print(f"[Sell] Using best bid price: {price_f}")
                    except Exception as e:
                        print(f"[Sell] Could not get orderbook: {e}")

                    # Для продажи: если у нас меньше акций чем минимум —
                    # всё равно пытаемся продать все что есть
                    # (CLOB может позволить продать остаток)

                    order_args = OrderArgs(
                        token_id=token_id,
                        size=size_rounded,
                        side="SELL",
                        price=price_f,
                    )

                    print(f"[Sell] Placing SELL: token={token_id[:16]}... "
                          f"size={size_rounded} shares, price={price_f}")

                    signed_order = py_clob.create_order(order_args)
                    resp = py_clob.post_order(signed_order, OrderType.GTC)
                    print(f"[Sell] CLOB response: {resp}")

                    if resp and resp.get("orderID"):
                        order_id = resp["orderID"]
                    elif resp and resp.get("success") is False:
                        exec_error = resp.get("errorMsg", "CLOB rejected the sell order")
                    elif resp and resp.get("errorMsg"):
                        exec_error = resp["errorMsg"]
                    else:
                        exec_error = f"Unexpected CLOB response: {resp}"

        except ImportError:
            exec_error = "py-clob-client not installed"
        except Exception as e:
            exec_error = str(e)
            print(f"[Sell] Exception: {exec_error}")

    # ── Результат ──────────────────────────────────────────────────────
    if exec_error:
        if lang == "ru":
            text = (
                f"❌ <b>Ордер на продажу не размещён</b>\n\n"
                f"<i>{exec_error}</i>\n\n"
                f"Попробуй через polymarket.com или обратись в @PolyScoreSupport"
            )
        else:
            text = (
                f"❌ <b>Sell order not placed</b>\n\n"
                f"<i>{exec_error}</i>\n\n"
                f"Try via polymarket.com or contact @PolyScoreSupport"
            )
        keyboard = [[InlineKeyboardButton(
            "📊 Портфель" if lang == "ru" else "📊 Portfolio",
            callback_data="portfolio"
        )]]
    else:
        q_short = question[:55] + "…" if len(question) > 55 else question
        outcome_emoji = "✅" if outcome.upper() == "YES" else "❌"
        sell_val = size * cur_price

        if lang == "ru":
            text = (
                f"💰 <b>Ордер на продажу размещён</b>\n\n"
                f"{outcome_emoji} <b>{outcome}</b>  ·  {size:.2f} шт.\n\n"
                f"<i>{q_short}</i>\n\n"
                f"Цена: <b>${cur_price:.2f}</b>  →  ~<b>${sell_val:.2f}</b>\n\n"
                f"🔑 <i>Order ID: {order_id[:16]}…</i>"
            )
        else:
            text = (
                f"💰 <b>Sell order placed</b>\n\n"
                f"{outcome_emoji} <b>{outcome}</b>  ·  {size:.2f} shares\n\n"
                f"<i>{q_short}</i>\n\n"
                f"Price: <b>${cur_price:.2f}</b>  →  ~<b>${sell_val:.2f}</b>\n\n"
                f"🔑 <i>Order ID: {order_id[:16]}…</i>"
            )
        keyboard = [[
            InlineKeyboardButton(
                "📊 Портфель" if lang == "ru" else "📊 Portfolio",
                callback_data="portfolio"
            ),
            InlineKeyboardButton(
                "🔥 Рынки" if lang == "ru" else "🔥 Markets",
                callback_data="cat:trending"
            ),
        ]]

    ctx.user_data.pop("sell", None)

    try:
        await query.edit_message_text(text, parse_mode="HTML",
                                       reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception:
        await query.message.reply_html(text,
                                        reply_markup=InlineKeyboardMarkup(keyboard))


async def cb_sell_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Callback: sell:cancel — отмена продажи, возврат в портфель."""
    query = update.callback_query
    await query.answer()
    ctx.user_data.pop("sell", None)
    # Возвращаемся в портфель
    from handlers.portfolio import cb_portfolio
    await cb_portfolio(update, ctx)
