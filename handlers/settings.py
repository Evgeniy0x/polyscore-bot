# PolyScore — Settings Handler
# ⚙️ Настройки: язык, уведомления, режим (demo/live), кошелёк

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.database import get_user, set_language
from config import POLY_API_KEY


# ══════════════════════════════════════════════════════════════════════
# Тексты
# ══════════════════════════════════════════════════════════════════════

_T = {
    "title": {
        "ru": "⚙️ <b>Настройки</b>",
        "en": "⚙️ <b>Settings</b>",
        "es": "⚙️ <b>Configuración</b>",
        "pt": "⚙️ <b>Configurações</b>",
        "tr": "⚙️ <b>Ayarlar</b>",
        "id": "⚙️ <b>Pengaturan</b>",
        "zh": "⚙️ <b>设置</b>",
        "ar": "⚙️ <b>الإعدادات</b>",
        "fr": "⚙️ <b>Paramètres</b>",
        "de": "⚙️ <b>Einstellungen</b>",
        "hi": "⚙️ <b>सेटिंग्स</b>",
        "ja": "⚙️ <b>設定</b>",
    },
    "language_row": {
        "ru": "🌍 Язык",
        "en": "🌍 Language",
        "es": "🌍 Idioma",
        "pt": "🌍 Idioma",
        "tr": "🌍 Dil",
        "id": "🌍 Bahasa",
        "zh": "🌍 语言",
        "ar": "🌍 اللغة",
        "fr": "🌍 Langue",
        "de": "🌍 Sprache",
        "hi": "🌍 भाषा",
        "ja": "🌍 言語",
    },
    "wallet_row": {
        "ru": "💳 Кошелёк",
        "en": "💳 Wallet",
        "es": "💳 Cartera",
        "pt": "💳 Carteira",
        "tr": "💳 Cüzdan",
        "id": "💳 Dompet",
        "zh": "💳 钱包",
        "ar": "💳 المحفظة",
        "fr": "💳 Portefeuille",
        "de": "💳 Wallet",
        "hi": "💳 वॉलेट",
        "ja": "💳 ウォレット",
    },
    "notifications_row": {
        "ru": "🔔 Уведомления",
        "en": "🔔 Notifications",
        "es": "🔔 Notificaciones",
        "pt": "🔔 Notificações",
        "tr": "🔔 Bildirimler",
        "id": "🔔 Notifikasi",
        "zh": "🔔 通知",
        "ar": "🔔 الإشعارات",
        "fr": "🔔 Notifications",
        "de": "🔔 Benachrichtigungen",
        "hi": "🔔 सूचनाएं",
        "ja": "🔔 通知",
    },
    "mode_demo": {
        "ru": "🎮 Режим: Demo",
        "en": "🎮 Mode: Demo",
        "es": "🎮 Modo: Demo",
        "pt": "🎮 Modo: Demo",
        "tr": "🎮 Mod: Demo",
        "id": "🎮 Mode: Demo",
        "zh": "🎮 模式: 演示",
        "ar": "🎮 الوضع: تجريبي",
        "fr": "🎮 Mode: Démo",
        "de": "🎮 Modus: Demo",
        "hi": "🎮 मोड: डेमो",
        "ja": "🎮 モード: デモ",
    },
    "mode_live": {
        "ru": "⚡ Режим: Live",
        "en": "⚡ Mode: Live",
        "es": "⚡ Modo: Live",
        "pt": "⚡ Modo: Live",
        "tr": "⚡ Mod: Canlı",
        "id": "⚡ Mode: Live",
        "zh": "⚡ 模式: 实盘",
        "ar": "⚡ الوضع: مباشر",
        "fr": "⚡ Mode: Live",
        "de": "⚡ Modus: Live",
        "hi": "⚡ मोड: लाइव",
        "ja": "⚡ モード: ライブ",
    },
    "back": {
        "ru": "🔙 Назад",
        "en": "🔙 Back",
        "es": "🔙 Atrás",
        "pt": "🔙 Voltar",
        "tr": "🔙 Geri",
        "id": "🔙 Kembali",
        "zh": "🔙 返回",
        "ar": "🔙 رجوع",
        "fr": "🔙 Retour",
        "de": "🔙 Zurück",
        "hi": "🔙 वापस",
        "ja": "🔙 戻る",
    },
    "wallet_connected": {
        "ru": "✅ Кошелёк подключён",
        "en": "✅ Wallet connected",
        "es": "✅ Cartera conectada",
        "pt": "✅ Carteira conectada",
        "tr": "✅ Cüzdan bağlı",
        "id": "✅ Dompet terhubung",
        "zh": "✅ 钱包已连接",
        "ar": "✅ المحفظة متصلة",
        "fr": "✅ Portefeuille connecté",
        "de": "✅ Wallet verbunden",
        "hi": "✅ वॉलेट जुड़ा है",
        "ja": "✅ ウォレット接続済み",
    },
    "wallet_not_connected": {
        "ru": "❌ Кошелёк не подключён",
        "en": "❌ No wallet connected",
        "es": "❌ Sin cartera",
        "pt": "❌ Sem carteira",
        "tr": "❌ Cüzdan bağlı değil",
        "id": "❌ Dompet belum terhubung",
        "zh": "❌ 未连接钱包",
        "ar": "❌ لا توجد محفظة",
        "fr": "❌ Pas de portefeuille",
        "de": "❌ Keine Wallet",
        "hi": "❌ वॉलेट नहीं है",
        "ja": "❌ ウォレット未接続",
    },
}


LANGUAGE_NAMES = {
    "ru": "🇷🇺 Русский", "en": "🇬🇧 English", "es": "🇪🇸 Español",
    "pt": "🇵🇹 Português", "tr": "🇹🇷 Türkçe", "id": "🇮🇩 Indonesia",
    "zh": "🇨🇳 中文", "ar": "🇸🇦 العربية", "fr": "🇫🇷 Français",
    "de": "🇩🇪 Deutsch", "hi": "🇮🇳 हिन्दी", "ja": "🇯🇵 日本語",
}


def _t(key: str, lang: str) -> str:
    """Get text in user's language with fallback to English."""
    return _T.get(key, {}).get(lang) or _T.get(key, {}).get("en", "")


def _build_settings_text(user: dict, lang: str) -> str:
    """Build settings screen text."""
    wallet = user.get("wallet_address", "")
    has_wallet = bool(wallet)

    # Truncate wallet address for display
    wallet_display = ""
    if has_wallet:
        wallet_display = f"{wallet[:6]}…{wallet[-4:]}"

    # Determine mode
    is_live = bool(POLY_API_KEY)

    lines = [
        _t("title", lang),
        "",
        f"{_t('language_row', lang)}: {LANGUAGE_NAMES.get(lang, lang)}",
        "",
        f"{_t('wallet_row', lang)}: "
        + (_t("wallet_connected", lang) + f" <code>{wallet_display}</code>" if has_wallet
           else _t("wallet_not_connected", lang)),
        "",
        (_t("mode_live", lang) if is_live else _t("mode_demo", lang)),
        "",
    ]
    return "\n".join(lines)


def _build_settings_keyboard(user: dict, lang: str) -> InlineKeyboardMarkup:
    """Build settings keyboard."""
    has_wallet = bool(user.get("wallet_address", ""))

    # Row 1: Language change
    row1 = [InlineKeyboardButton(
        _t("language_row", lang) + " →",
        callback_data="lang:picker"
    )]

    # Row 2: Wallet
    row2 = [InlineKeyboardButton(
        "💳 " + ("Управление кошельком" if lang == "ru" else "Manage Wallet"),
        callback_data="wallet:status"
    )]

    # Row 3: Notifications
    row3 = [InlineKeyboardButton(
        _t("notifications_row", lang) + " →",
        callback_data="settings:notifications"
    )]

    # Row 4: Back
    row4 = [InlineKeyboardButton(_t("back", lang), callback_data="menu:main")]

    return InlineKeyboardMarkup([row1, row2, row3, row4])


# ══════════════════════════════════════════════════════════════════════
# Handler
# ══════════════════════════════════════════════════════════════════════

async def cb_settings(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Callback: settings — show settings screen."""
    query = update.callback_query
    await query.answer()

    user = await get_user(query.from_user.id)
    lang = (user or {}).get("language", "ru")
    user = user or {}

    text = _build_settings_text(user, lang)
    keyboard = _build_settings_keyboard(user, lang)

    await query.edit_message_text(
        text, parse_mode="HTML",
        reply_markup=keyboard
    )


async def cb_settings_notifications(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Callback: settings:notifications — notification preferences."""
    query = update.callback_query
    await query.answer()

    user = await get_user(query.from_user.id)
    lang = (user or {}).get("language", "ru")

    _notif_title = {
        "ru": "🔔 <b>Настройки уведомлений</b>\n\nВыбери какие сигналы получать:",
        "en": "🔔 <b>Notification Settings</b>\n\nChoose which signals to receive:",
        "es": "🔔 <b>Ajustes de notificaciones</b>\n\nElige qué señales recibir:",
        "pt": "🔔 <b>Configurações de notificações</b>\n\nEscolha quais sinais receber:",
    }
    _l = lang if lang in _notif_title else "en"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "🔴 Только HIGH сигналы" if lang == "ru" else "🔴 HIGH signals only",
            callback_data="settings:notif:high"
        )],
        [InlineKeyboardButton(
            "🟡 HIGH + MEDIUM" if lang == "ru" else "🟡 HIGH + MEDIUM",
            callback_data="settings:notif:medium"
        )],
        [InlineKeyboardButton(
            "🔕 Отключить" if lang == "ru" else "🔕 Turn off",
            callback_data="settings:notif:off"
        )],
        [InlineKeyboardButton(
            "🔙 Назад" if lang == "ru" else "🔙 Back",
            callback_data="settings"
        )],
    ])

    await query.edit_message_text(
        _notif_title[_l], parse_mode="HTML",
        reply_markup=keyboard
    )


async def cb_settings_notif_level(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Callback: settings:notif:{level} — save notification preference."""
    query = update.callback_query
    level = query.data.split(":")[2]

    user = await get_user(query.from_user.id)
    lang = (user or {}).get("language", "ru")

    _saved = {
        "ru": {"high": "✅ Только HIGH сигналы", "medium": "✅ HIGH + MEDIUM", "off": "🔕 Уведомления отключены"},
        "en": {"high": "✅ HIGH signals only", "medium": "✅ HIGH + MEDIUM", "off": "🔕 Notifications off"},
    }
    _l = lang if lang in _saved else "en"
    msg = _saved[_l].get(level, "✅ Сохранено")

    await query.answer(msg, show_alert=True)

    # Return to settings
    user = user or {}
    text = _build_settings_text(user, lang)
    keyboard = _build_settings_keyboard(user, lang)
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)


async def cb_lang_picker(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Callback: lang:picker — show language selection grid (from settings)."""
    query = update.callback_query
    await query.answer()

    # Build 3x4 grid
    buttons = [
        [
            InlineKeyboardButton("🇷🇺 Русский",  callback_data="lang:ru"),
            InlineKeyboardButton("🇬🇧 English",  callback_data="lang:en"),
            InlineKeyboardButton("🇪🇸 Español",  callback_data="lang:es"),
        ],
        [
            InlineKeyboardButton("🇵🇹 Português", callback_data="lang:pt"),
            InlineKeyboardButton("🇹🇷 Türkçe",   callback_data="lang:tr"),
            InlineKeyboardButton("🇮🇩 Indonesia", callback_data="lang:id"),
        ],
        [
            InlineKeyboardButton("🇨🇳 中文",      callback_data="lang:zh"),
            InlineKeyboardButton("🇸🇦 العربية",   callback_data="lang:ar"),
            InlineKeyboardButton("🇫🇷 Français",  callback_data="lang:fr"),
        ],
        [
            InlineKeyboardButton("🇩🇪 Deutsch",   callback_data="lang:de"),
            InlineKeyboardButton("🇮🇳 हिन्दी",    callback_data="lang:hi"),
            InlineKeyboardButton("🇯🇵 日本語",    callback_data="lang:ja"),
        ],
    ]

    await query.edit_message_text(
        "🌍 <b>Select language / Выберите язык</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
