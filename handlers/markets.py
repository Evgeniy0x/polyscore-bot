# PolyScore — Handlers для просмотра рынков
# ВСЕ категории Polymarket: спорт, крипто, политика, поп-культура, бизнес, наука
#
# Архитектура меню:
#   📊 Рынки (cat:markets) → верхний уровень с категориями
#     ├── 🏆 Спорт (cat:sports) → подменю видов спорта
#     ├── ₿ Крипто (tag:crypto)
#     ├── 🏛️ Политика (tag:politics)
#     ├── 🎬 Поп-культура (tag:pop-culture)
#     ├── 💼 Бизнес (tag:business)
#     ├── 🔬 Наука (tag:science)
#     └── 🔥 Trending (cat:trending) → горячие рынки со всех категорий
#
# КЛЮЧЕВОЙ ПРИНЦИП: Telegram ограничивает callback_data до 64 байт.
# Решение: храним рынки в ctx.bot_data["mc"] по короткому ключу (m:0, m:1...)

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.polymarket import gamma, format_volume, price_to_american_odds
from services.database import get_user, add_to_watchlist
from services.translator import translate_many, translate_market_name
from config import SPORT_TAGS, SPORT_EMOJI, MAX_MARKETS_PER_PAGE, CATEGORY_NAMES


# ──────────────────────────────────────────────────────────────────
# Кеш рынков: bot_data["mc"] = {0: {...}, 1: {...}, ...}
# ──────────────────────────────────────────────────────────────────

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


def _get_cached(ctx: ContextTypes.DEFAULT_TYPE, idx: int) -> dict:
    """Получить рынок из кеша по ключу."""
    return ctx.bot_data.get("mc", {}).get(idx, {})


# ══════════════════════════════════════════════════════════════════════
# Мультиязычные тексты для меню
# ══════════════════════════════════════════════════════════════════════

_HEADERS = {
    "markets": {
        "ru": "📊 <b>Рынки Polymarket</b>\nВыбери категорию:",
        "en": "📊 <b>Polymarket Markets</b>\nChoose a category:",
        "es": "📊 <b>Mercados Polymarket</b>\nElige una categoría:",
        "pt": "📊 <b>Mercados Polymarket</b>\nEscolha uma categoria:",
        "tr": "📊 <b>Polymarket Piyasaları</b>\nKategori seçin:",
        "id": "📊 <b>Pasar Polymarket</b>\nPilih kategori:",
        "zh": "📊 <b>Polymarket 市场</b>\n选择类别：",
        "ar": "📊 <b>أسواق Polymarket</b>\nاختر فئة:",
        "fr": "📊 <b>Marchés Polymarket</b>\nChoisissez une catégorie:",
        "de": "📊 <b>Polymarket Märkte</b>\nKategorie wählen:",
        "hi": "📊 <b>Polymarket बाजार</b>\nश्रेणी चुनें:",
        "ja": "📊 <b>Polymarket マーケット</b>\nカテゴリを選択:",
    },
    "sports": {
        "ru": "🏆 <b>Спортивные рынки</b>\nВыбери вид спорта:",
        "en": "🏆 <b>Sports Markets</b>\nChoose a sport:",
        "es": "🏆 <b>Mercados Deportivos</b>\nElige un deporte:",
        "pt": "🏆 <b>Mercados Esportivos</b>\nEscolha um esporte:",
        "tr": "🏆 <b>Spor Piyasaları</b>\nSpor seçin:",
        "id": "🏆 <b>Pasar Olahraga</b>\nPilih olahraga:",
        "zh": "🏆 <b>体育市场</b>\n选择运动项目：",
        "ar": "🏆 <b>الأسواق الرياضية</b>\nاختر رياضة:",
        "fr": "🏆 <b>Marchés Sportifs</b>\nChoisissez un sport:",
        "de": "🏆 <b>Sportmärkte</b>\nSportart wählen:",
        "hi": "🏆 <b>खेल बाजार</b>\nखेल चुनें:",
        "ja": "🏆 <b>スポーツマーケット</b>\nスポーツを選択:",
    },
    "trending": {
        "ru": "🔥 <b>Горячие рынки</b>\n",
        "en": "🔥 <b>Trending Markets</b>\n",
        "es": "🔥 <b>Mercados en Tendencia</b>\n",
        "pt": "🔥 <b>Mercados em Alta</b>\n",
        "tr": "🔥 <b>Trend Piyasalar</b>\n",
        "id": "🔥 <b>Pasar Trending</b>\n",
        "zh": "🔥 <b>热门市场</b>\n",
        "ar": "🔥 <b>الأسواق الرائجة</b>\n",
        "fr": "🔥 <b>Marchés Tendance</b>\n",
        "de": "🔥 <b>Trend-Märkte</b>\n",
        "hi": "🔥 <b>ट्रेंडिंग बाजार</b>\n",
        "ja": "🔥 <b>トレンドマーケット</b>\n",
    },
}

# Кнопка "Назад" на всех языках
_BACK = {
    "ru": "🔙 Назад", "en": "🔙 Back", "es": "🔙 Atrás", "pt": "🔙 Voltar",
    "tr": "🔙 Geri", "id": "🔙 Kembali", "zh": "🔙 返回", "ar": "🔙 رجوع",
    "fr": "🔙 Retour", "de": "🔙 Zurück", "hi": "🔙 वापस", "ja": "🔙 戻る",
}


def _get_header(section: str, lang: str) -> str:
    return _HEADERS[section].get(lang, _HEADERS[section]["en"])

def _get_back(lang: str) -> str:
    return _BACK.get(lang, _BACK["en"])

def _get_cat_name(tag: str, lang: str) -> str:
    names = CATEGORY_NAMES.get(lang, CATEGORY_NAMES["en"])
    return names.get(tag, tag.capitalize())


# ══════════════════════════════════════════════════════════════════════
# Главное меню: Все категории
# ══════════════════════════════════════════════════════════════════════

def _build_markets_menu(lang: str) -> InlineKeyboardMarkup:
    """Собрать кнопки главного меню рынков."""
    keyboard = [
        # Ряд 1: Спорт (подменю) + Крипто
        [InlineKeyboardButton(f"🏆 {_get_cat_name('sports', lang)}", callback_data="cat:sports"),
         InlineKeyboardButton(f"₿ {_get_cat_name('crypto', lang)}", callback_data="tag:crypto")],
        # Ряд 2: Политика + Поп-культура
        [InlineKeyboardButton(f"🏛️ {_get_cat_name('politics', lang)}", callback_data="tag:politics"),
         InlineKeyboardButton(f"🎬 {_get_cat_name('pop-culture', lang)}", callback_data="tag:pop-culture")],
        # Ряд 3: Бизнес + Наука
        [InlineKeyboardButton(f"💼 {_get_cat_name('business', lang)}", callback_data="tag:business"),
         InlineKeyboardButton(f"🔬 {_get_cat_name('science', lang)}", callback_data="tag:science")],
        # Ряд 4: Trending
        [InlineKeyboardButton("🔥 Trending", callback_data="cat:trending")],
        # Назад
        [InlineKeyboardButton(_get_back(lang), callback_data="menu:main")],
    ]
    return InlineKeyboardMarkup(keyboard)


def _build_sports_menu(lang: str) -> InlineKeyboardMarkup:
    """Собрать кнопки подменю спорта."""
    keyboard = [
        [InlineKeyboardButton(f"⚾ {_get_cat_name('baseball', lang)}", callback_data="tag:baseball"),
         InlineKeyboardButton(f"🏀 {_get_cat_name('basketball', lang)}", callback_data="tag:basketball")],
        [InlineKeyboardButton(f"🏒 {_get_cat_name('hockey', lang)}", callback_data="tag:hockey"),
         InlineKeyboardButton(f"⚽ {_get_cat_name('soccer', lang)}", callback_data="tag:soccer")],
        [InlineKeyboardButton(f"🏈 {_get_cat_name('football', lang)}", callback_data="tag:football"),
         InlineKeyboardButton(f"🥊 {_get_cat_name('mma', lang)}", callback_data="tag:mma")],
        [InlineKeyboardButton(f"🎾 {_get_cat_name('tennis', lang)}", callback_data="tag:tennis"),
         InlineKeyboardButton(f"🏆 {_get_cat_name('sports', lang)}", callback_data="tag:sports")],
        # Назад в главное меню рынков
        [InlineKeyboardButton(_get_back(lang), callback_data="cat:markets")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ══════════════════════════════════════════════════════════════════════
# Handlers
# ══════════════════════════════════════════════════════════════════════

async def cmd_sports(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Команда /sports — теперь открывает ВСЕ рынки, не только спорт."""
    user = await get_user(update.effective_user.id)
    lang = (user or {}).get("language", "ru")
    await update.message.reply_html(
        _get_header("markets", lang),
        reply_markup=_build_markets_menu(lang),
    )


async def cb_markets_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Callback: cat:markets — главное меню рынков с категориями."""
    query = update.callback_query
    await query.answer()
    user = await get_user(query.from_user.id)
    lang = (user or {}).get("language", "ru")
    await query.edit_message_text(
        _get_header("markets", lang), parse_mode="HTML",
        reply_markup=_build_markets_menu(lang),
    )


async def cb_sports_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Callback: cat:sports — подменю спортивных категорий."""
    query = update.callback_query
    await query.answer()
    user = await get_user(query.from_user.id)
    lang = (user or {}).get("language", "ru")
    await query.edit_message_text(
        _get_header("sports", lang), parse_mode="HTML",
        reply_markup=_build_sports_menu(lang),
    )


async def cb_tag_markets(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Callback: tag:{category} или tag:{category}:{page} — рынки по категории."""
    query = update.callback_query
    await query.answer("⏳ Загружаю…")

    parts = query.data.split(":")
    tag = parts[1]
    page = int(parts[2]) if len(parts) > 2 else 0
    offset = page * MAX_MARKETS_PER_PAGE

    user = await get_user(query.from_user.id)
    lang = (user or {}).get("language", "ru")
    emoji = SPORT_EMOJI.get(tag, "📊")

    # Загружаем рынки через единый метод
    markets = await gamma.get_sports_markets(
        limit=MAX_MARKETS_PER_PAGE + 1, offset=offset, tag=tag
    )

    has_next = len(markets) > MAX_MARKETS_PER_PAGE
    markets = markets[:MAX_MARKETS_PER_PAGE]

    if not markets:
        no_text = "😔 Рынков не найдено." if lang == "ru" else "😔 No markets found."
        keyboard = [[InlineKeyboardButton(_get_back(lang), callback_data="cat:markets")]]
        await query.edit_message_text(
            no_text, reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    cat_name = _get_cat_name(tag, lang)
    lines = [f"{emoji} <b>{cat_name}</b>", ""]
    cached_ids = []

    # Переводим названия рынков
    raw_questions = [m.get("question", m.get("title", "—")) for m in markets]
    translated_questions = await translate_many(raw_questions, lang)

    for i, m in enumerate(markets):
        idx = _cache_market(ctx, m)
        cached_ids.append(idx)
        q = translated_questions[i]
        yes_p, _ = gamma.extract_prices(m)
        v24 = float(m.get("volume24hr", 0) or 0)
        if len(q) > 55:
            q = q[:52] + "…"
        mood = "🟢" if yes_p >= 0.65 else ("🟡" if yes_p >= 0.35 else "🔴")
        lines.append(f"{mood} {q}")
        lines.append(f"   YES <b>{yes_p:.0%}</b>  ·  {format_volume(v24)}/24ч")
        lines.append("")

    text = "\n".join(lines)

    # Кнопки рынков
    market_buttons = []
    for i, idx in enumerate(cached_ids):
        m = markets[i]
        q_btn = m.get("question", m.get("title", ""))[:30]
        if len(m.get("question", m.get("title", ""))) > 30:
            q_btn += "…"
        market_buttons.append([
            InlineKeyboardButton(f"{i+1}. {q_btn}", callback_data=f"m:{idx}")
        ])

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("◀", callback_data=f"tag:{tag}:{page-1}"))
    if has_next:
        nav_row.append(InlineKeyboardButton("▶", callback_data=f"tag:{tag}:{page+1}"))

    keyboard = market_buttons
    if nav_row:
        keyboard.append(nav_row)

    # Кнопка "Назад" — если спортивный тег → обратно в спорт, иначе в рынки
    back_target = "cat:sports" if tag in SPORT_TAGS else "cat:markets"
    keyboard.append([
        InlineKeyboardButton("🎯 Парлей", callback_data="parlay:new"),
        InlineKeyboardButton(_get_back(lang), callback_data=back_target),
    ])

    await query.edit_message_text(
        text, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def cb_trending(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Callback: cat:trending — горячие рынки со ВСЕХ категорий."""
    query = update.callback_query
    await query.answer("🔥 Загружаю…")

    user = await get_user(query.from_user.id)
    lang = (user or {}).get("language", "ru")

    # Теперь без фильтра — берём топ по объёму со всех категорий
    markets = await gamma.get_trending_markets(limit=8)

    header = _get_header("trending", lang)
    lines = [header]
    cached_ids = []
    for m in markets[:8]:
        idx = _cache_market(ctx, m)
        cached_ids.append(idx)
        q = m.get("question", m.get("title", "—"))
        yes_p, _ = gamma.extract_prices(m)
        v24 = float(m.get("volume24hr", 0) or 0)

        # Определяем иконку по категории
        cat_emj = "📊"
        combined = (m.get("_event_title", "") + q).lower()
        for cat_key, sp_emoji in SPORT_EMOJI.items():
            if cat_key in combined:
                cat_emj = sp_emoji
                break

        if len(q) > 50:
            q = q[:47] + "…"
        lines.append(f"{cat_emj} {q}")
        lines.append(f"   YES <b>{yes_p:.0%}</b>  ·  {format_volume(v24)}")
        lines.append("")

    text = "\n".join(lines)

    keyboard = []
    for i, idx in enumerate(cached_ids):
        m = markets[i] if i < len(markets) else {}
        q_btn = m.get("question", m.get("title", ""))[:28] + "…"
        keyboard.append([InlineKeyboardButton(
            f"{i+1}. {q_btn}", callback_data=f"m:{idx}"
        )])
    keyboard.append([
        InlineKeyboardButton("📊 " + ("Рынки" if lang == "ru" else "Markets"), callback_data="cat:markets"),
        InlineKeyboardButton(_get_back(lang), callback_data="menu:main"),
    ])

    await query.edit_message_text(
        text, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def cb_market_detail(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    Callback: m:{idx} — детали рынка из кеша.
    Показывает цены, odds, кнопки Buy YES/NO, AI, Watchlist.
    """
    query = update.callback_query
    await query.answer("📊 Загружаю…")

    idx = int(query.data.split(":")[1])
    market = _get_cached(ctx, idx)

    user = await get_user(query.from_user.id)
    lang = (user or {}).get("language", "ru")

    # Fix #3: graceful fallback если кеш пустой (перезапуск бота)
    if not market:
        _cache_msg = {
            "ru": "🔄 <b>Список рынков обновился</b>\n\nВыбери категорию снова — займёт секунду.",
            "en": "🔄 <b>Market list has refreshed</b>\n\nPlease browse a category again — takes a second.",
            "es": "🔄 <b>Lista de mercados actualizada</b>\n\nElige una categoría de nuevo.",
            "pt": "🔄 <b>Lista de mercados atualizada</b>\n\nEscolha uma categoria novamente.",
        }
        _l = lang if lang in _cache_msg else "en"
        await query.edit_message_text(
            _cache_msg[_l], parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 " + ("Рынки" if lang == "ru" else "Markets"), callback_data="cat:markets")],
                [InlineKeyboardButton("🔥 Trending", callback_data="cat:trending")],
            ])
        )
        return

    question = market.get("question", market.get("title", "—"))
    question = await translate_market_name(question, lang)
    desc = (market.get("description") or "")[:200]
    end_date = (market.get("endDate") or "")[:10]
    volume = float(market.get("volume", 0) or 0)
    volume24 = float(market.get("volume24hr", 0) or 0)

    yes_price, no_price = gamma.extract_prices(market)
    yes_odds = price_to_american_odds(yes_price)
    no_odds = price_to_american_odds(no_price)
    mood = "🟢" if yes_price >= 0.65 else ("🟡" if yes_price >= 0.35 else "🔴")

    if lang == "ru":
        text = (
            f"{mood} <b>{question}</b>\n\n"
            f"<b>YES</b>  {yes_price:.0%}  <code>{yes_odds}</code>   "
            f"<b>NO</b>  {no_price:.0%}  <code>{no_odds}</code>\n\n"
            f"💰 Объём: <b>{format_volume(volume)}</b>  "
            f"·  24ч: <b>{format_volume(volume24)}</b>\n"
            f"📅 Закрывается: <b>{end_date or '—'}</b>\n"
        )
        if desc:
            text += f"\n📝 {desc[:150]}…" if len(desc) > 150 else f"\n📝 {desc}"
    else:
        text = (
            f"{mood} <b>{question}</b>\n\n"
            f"<b>YES</b>  {yes_price:.0%}  <code>{yes_odds}</code>   "
            f"<b>NO</b>  {no_price:.0%}  <code>{no_odds}</code>\n\n"
            f"💰 Volume: <b>{format_volume(volume)}</b>  "
            f"·  24h: <b>{format_volume(volume24)}</b>\n"
            f"📅 Closes: <b>{end_date or '—'}</b>\n"
        )
        if desc:
            text += f"\n📝 {desc[:150]}…" if len(desc) > 150 else f"\n📝 {desc}"

    keyboard = [
        [
            InlineKeyboardButton(
                f"✅ YES {yes_price:.0%} ({yes_odds})",
                callback_data=f"b:Y:{idx}"
            ),
            InlineKeyboardButton(
                f"❌ NO {no_price:.0%} ({no_odds})",
                callback_data=f"b:N:{idx}"
            ),
        ],
        [
            InlineKeyboardButton("🤖 AI Анализ", callback_data=f"ai:{idx}"),
            InlineKeyboardButton("🎯 В парлей", callback_data=f"pl:{idx}"),
        ],
        [
            InlineKeyboardButton("⭐ Следить", callback_data=f"w:{idx}"),
            InlineKeyboardButton("🔔 Алерт", callback_data=f"alert:add:{idx}"),
        ],
        [
            InlineKeyboardButton(_get_back(lang), callback_data="cat:markets"),
        ],
    ]

    await query.edit_message_text(
        text, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def cb_watchlist_add(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Добавить рынок в избранное: callback w:{idx}."""
    query = update.callback_query
    idx = int(query.data.split(":")[1])
    market = _get_cached(ctx, idx)

    slug = market.get("slug", str(idx))
    question = market.get("question", market.get("title", slug))

    await add_to_watchlist(query.from_user.id, slug, question)

    user = await get_user(query.from_user.id)
    lang = (user or {}).get("language", "ru")
    msg = "⭐ Добавлено в избранное!" if lang == "ru" else "⭐ Added to watchlist!"
    await query.answer(msg, show_alert=True)
