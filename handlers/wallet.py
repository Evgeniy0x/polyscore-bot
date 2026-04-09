# PolyScore — Wallet handler
# Автоматическое создание Safe-кошелька через Polymarket Relayer API
# Пользователю нужно только пополнить кошелёк USDC

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.database import get_user, update_user_wallet, save_generated_wallet
from services.polymarket import relayer


# States for ConversationHandler (manual address input fallback)
WAIT_WALLET_ADDRESS = 1


# ══════════════════════════════════════════════════════════════════════
# Мультиязычные тексты
# ══════════════════════════════════════════════════════════════════════

T = {
    "wallet_title": {
        "ru": "💳 <b>Мой кошелёк</b>",
        "en": "💳 <b>My Wallet</b>",
        "es": "💳 <b>Mi Cartera</b>",
        "pt": "💳 <b>Minha Carteira</b>",
        "tr": "💳 <b>Cüzdanım</b>",
        "id": "💳 <b>Dompet Saya</b>",
        "zh": "💳 <b>我的钱包</b>",
        "ar": "💳 <b>محفظتي</b>",
        "fr": "💳 <b>Mon Portefeuille</b>",
        "de": "💳 <b>Meine Wallet</b>",
        "hi": "💳 <b>मेरा वॉलेट</b>",
        "ja": "💳 <b>マイウォレット</b>",
    },
    "no_wallet": {
        "ru": (
            "У тебя ещё нет кошелька.\n\n"
            "🚀 <b>Создать автоматически</b> — бот создаст кошелёк за тебя прямо сейчас.\n"
            "Тебе останется только пополнить его USDC.\n\n"
            "или\n\n"
            "📲 <b>Подключить свой</b> — введи адрес существующего кошелька (0x...)"
        ),
        "en": (
            "You don't have a wallet yet.\n\n"
            "🚀 <b>Create automatically</b> — the bot will create a wallet for you right now.\n"
            "You'll just need to fund it with USDC.\n\n"
            "or\n\n"
            "📲 <b>Connect existing</b> — enter your wallet address (0x...)"
        ),
        "es": (
            "Aún no tienes una cartera.\n\n"
            "🚀 <b>Crear automáticamente</b> — el bot creará una cartera para ti ahora mismo.\n"
            "Solo necesitarás cargarla con USDC.\n\n"
            "o\n\n"
            "📲 <b>Conectar existente</b> — ingresa tu dirección de cartera (0x...)"
        ),
        "pt": (
            "Você ainda não tem uma carteira.\n\n"
            "🚀 <b>Criar automaticamente</b> — o bot criará uma carteira para você agora.\n"
            "Você só precisará financiá-la com USDC.\n\n"
            "ou\n\n"
            "📲 <b>Conectar existente</b> — insira seu endereço de carteira (0x...)"
        ),
        "tr": (
            "Henüz bir cüzdanınız yok.\n\n"
            "🚀 <b>Otomatik oluştur</b> — bot şimdi sizin için bir cüzdan oluşturacak.\n"
            "Sadece USDC ile doldurmanız yeterli.\n\n"
            "veya\n\n"
            "📲 <b>Mevcut cüzdanı bağla</b> — cüzdan adresinizi girin (0x...)"
        ),
        "id": (
            "Anda belum memiliki dompet.\n\n"
            "🚀 <b>Buat otomatis</b> — bot akan membuat dompet untuk Anda sekarang.\n"
            "Anda hanya perlu mengisi USDC.\n\n"
            "atau\n\n"
            "📲 <b>Hubungkan yang ada</b> — masukkan alamat dompet Anda (0x...)"
        ),
        "zh": (
            "您还没有钱包。\n\n"
            "🚀 <b>自动创建</b> — 机器人现在会为您创建钱包。\n"
            "您只需要充值 USDC。\n\n"
            "或\n\n"
            "📲 <b>连接现有钱包</b> — 输入您的钱包地址 (0x...)"
        ),
        "ar": (
            "ليس لديك محفظة بعد.\n\n"
            "🚀 <b>إنشاء تلقائي</b> — سيقوم البوت بإنشاء محفظة لك الآن.\n"
            "ستحتاج فقط إلى تمويلها بـ USDC.\n\n"
            "أو\n\n"
            "📲 <b>ربط محفظة موجودة</b> — أدخل عنوان محفظتك (0x...)"
        ),
        "fr": (
            "Vous n'avez pas encore de portefeuille.\n\n"
            "🚀 <b>Créer automatiquement</b> — le bot créera un portefeuille pour vous maintenant.\n"
            "Vous n'aurez qu'à l'alimenter en USDC.\n\n"
            "ou\n\n"
            "📲 <b>Connecter l'existant</b> — entrez votre adresse de portefeuille (0x...)"
        ),
        "de": (
            "Sie haben noch keine Wallet.\n\n"
            "🚀 <b>Automatisch erstellen</b> — der Bot erstellt jetzt eine Wallet für Sie.\n"
            "Sie müssen sie nur mit USDC aufladen.\n\n"
            "oder\n\n"
            "📲 <b>Vorhandene verbinden</b> — geben Sie Ihre Wallet-Adresse ein (0x...)"
        ),
        "hi": (
            "आपके पास अभी तक कोई वॉलेट नहीं है।\n\n"
            "🚀 <b>स्वतः बनाएं</b> — बॉट अभी आपके लिए वॉलेट बनाएगा।\n"
            "आपको बस USDC से फंड करना होगा।\n\n"
            "या\n\n"
            "📲 <b>मौजूदा कनेक्ट करें</b> — अपना वॉलेट पता दर्ज करें (0x...)"
        ),
        "ja": (
            "まだウォレットがありません。\n\n"
            "🚀 <b>自動作成</b> — ボットが今すぐウォレットを作成します。\n"
            "あとはUSDCで入金するだけです。\n\n"
            "または\n\n"
            "📲 <b>既存を接続</b> — ウォレットアドレスを入力 (0x...)"
        ),
    },
    "creating_wallet": {
        "ru": "⏳ Создаю кошелёк... Подожди пару секунд.",
        "en": "⏳ Creating wallet... Please wait a moment.",
        "es": "⏳ Creando cartera... Espera un momento.",
        "pt": "⏳ Criando carteira... Aguarde um momento.",
        "tr": "⏳ Cüzdan oluşturuluyor... Lütfen bekleyin.",
        "id": "⏳ Membuat dompet... Tunggu sebentar.",
        "zh": "⏳ 正在创建钱包... 请稍等。",
        "ar": "⏳ جارٍ إنشاء المحفظة... انتظر لحظة.",
        "fr": "⏳ Création du portefeuille... Veuillez patienter.",
        "de": "⏳ Wallet wird erstellt... Bitte warten.",
        "hi": "⏳ वॉलेट बनाया जा रहा है... कृपया प्रतीक्षा करें।",
        "ja": "⏳ ウォレットを作成中... しばらくお待ちください。",
    },
    "wallet_created": {
        "ru": (
            "✅ <b>Кошелёк создан!</b>\n\n"
            "📋 Адрес:\n<code>{address}</code>\n\n"
            "💡 <b>Как пополнить:</b>\n"
            "1️⃣ Купи <b>USDC</b> на бирже (Binance, Bybit, Kraken)\n"
            "2️⃣ Выводи в сеть <b>Polygon (MATIC)</b> — не Ethereum!\n"
            "3️⃣ Укажи адрес выше\n"
            "4️⃣ Обычно 5-15 минут — и деньги на счету\n\n"
            "⚠️ Только сеть <b>Polygon</b>. Ethereum не подойдёт — деньги потеряются!\n\n"
            "🤖 <b>Включи AutoTrade</b> — алгоритм торгует за тебя 24/7. Мы берём 20% только с прибыли."
        ),
        "en": (
            "✅ <b>Wallet created!</b>\n\n"
            "📋 Address:\n<code>{address}</code>\n\n"
            "💡 <b>How to fund it:</b>\n"
            "1️⃣ Buy <b>USDC</b> on an exchange (Binance, Bybit, Kraken)\n"
            "2️⃣ Withdraw to <b>Polygon (MATIC)</b> network — not Ethereum!\n"
            "3️⃣ Use the address above\n"
            "4️⃣ Usually 5-15 minutes — funds arrive\n\n"
            "⚠️ <b>Polygon network only.</b> Ethereum won't work — funds will be lost!\n\n"
            "🤖 <b>Enable AutoTrade</b> — algorithm trades for you 24/7. We take 20% only from profit."
        ),
        "es": (
            "✅ <b>¡Cartera creada!</b>\n\n"
            "📋 Dirección:\n<code>{address}</code>\n\n"
            "💡 <b>Cómo financiarla:</b>\n"
            "1️⃣ Compra <b>USDC</b> en un exchange (Binance, Bybit, Kraken)\n"
            "2️⃣ Retira a la red <b>Polygon (MATIC)</b> — ¡no Ethereum!\n"
            "3️⃣ Usa la dirección de arriba\n"
            "4️⃣ Normalmente 5-15 minutos — fondos disponibles\n\n"
            "⚠️ <b>Solo red Polygon.</b> Ethereum no funcionará — ¡perderás los fondos!\n\n"
            "🤖 <b>Activa AutoTrade</b> — el algoritmo opera por ti 24/7. Solo 20% de las ganancias."
        ),
        "pt": (
            "✅ <b>Carteira criada!</b>\n\n"
            "📋 Endereço:\n<code>{address}</code>\n\n"
            "💡 <b>Como financiar:</b>\n"
            "1️⃣ Compre <b>USDC</b> em uma exchange (Binance, Bybit, Kraken)\n"
            "2️⃣ Retire para a rede <b>Polygon (MATIC)</b> — não Ethereum!\n"
            "3️⃣ Use o endereço acima\n"
            "4️⃣ Normalmente 5-15 minutos — fundos chegam\n\n"
            "⚠️ <b>Apenas rede Polygon.</b> Ethereum não funciona — fundos serão perdidos!\n\n"
            "🤖 <b>Ative o AutoTrade</b> — algoritmo opera por você 24/7. Apenas 20% dos lucros."
        ),
        "tr": (
            "✅ <b>Cüzdan oluşturuldu!</b>\n\n"
            "📋 Adres:\n<code>{address}</code>\n\n"
            "💡 <b>Nasıl yükleyebilirim:</b>\n"
            "1️⃣ Bir borsada <b>USDC</b> satın alın (Binance, Bybit, Kraken)\n"
            "2️⃣ <b>Polygon (MATIC)</b> ağına çekin — Ethereum değil!\n"
            "3️⃣ Yukarıdaki adresi kullanın\n"
            "4️⃣ Genellikle 5-15 dakika — para gelir\n\n"
            "⚠️ <b>Sadece Polygon ağı.</b> Ethereum çalışmaz — para kaybolur!\n\n"
            "🤖 <b>AutoTrade'i etkinleştirin</b> — algoritma 7/24 sizin için işlem yapar. Sadece kârdan %20."
        ),
        "id": (
            "✅ <b>Dompet dibuat!</b>\n\n"
            "📋 Alamat:\n<code>{address}</code>\n\n"
            "💡 <b>Cara mengisi:</b>\n"
            "1️⃣ Beli <b>USDC</b> di bursa (Binance, Bybit, Kraken)\n"
            "2️⃣ Tarik ke jaringan <b>Polygon (MATIC)</b> — bukan Ethereum!\n"
            "3️⃣ Gunakan alamat di atas\n"
            "4️⃣ Biasanya 5-15 menit — dana masuk\n\n"
            "⚠️ <b>Hanya jaringan Polygon.</b> Ethereum tidak akan berfungsi — dana hilang!\n\n"
            "🤖 <b>Aktifkan AutoTrade</b> — algoritma trading untuk Anda 24/7. Hanya 20% dari profit."
        ),
        "zh": (
            "✅ <b>钱包已创建！</b>\n\n"
            "📋 地址：\n<code>{address}</code>\n\n"
            "💡 <b>如何充值：</b>\n"
            "1️⃣ 在交易所购买 <b>USDC</b>（Binance, Bybit, Kraken）\n"
            "2️⃣ 提币到 <b>Polygon (MATIC)</b> 网络，不是 Ethereum！\n"
            "3️⃣ 使用上面的地址\n"
            "4️⃣ 通常 5-15 分钟，资金到账\n\n"
            "⚠️ <b>仅限 Polygon 网络。</b>Ethereum 不可用，资金将丢失！\n\n"
            "🤖 <b>开启 AutoTrade</b> — 算法24/7为您交易。仅从利润中收取20%。"
        ),
        "ar": (
            "✅ <b>تم إنشاء المحفظة!</b>\n\n"
            "📋 العنوان:\n<code>{address}</code>\n\n"
            "💡 <b>كيفية التمويل:</b>\n"
            "1️⃣ اشترِ <b>USDC</b> في بورصة (Binance, Bybit, Kraken)\n"
            "2️⃣ سحب إلى شبكة <b>Polygon (MATIC)</b> — ليس Ethereum!\n"
            "3️⃣ استخدم العنوان أعلاه\n"
            "4️⃣ عادةً 5-15 دقيقة — تصل الأموال\n\n"
            "⚠️ <b>شبكة Polygon فقط.</b> Ethereum لن تعمل — ستفقد الأموال!\n\n"
            "🤖 <b>فعّل AutoTrade</b> — الخوارزمية تتداول لك 24/7. فقط 20% من الأرباح."
        ),
        "fr": (
            "✅ <b>Portefeuille créé!</b>\n\n"
            "📋 Adresse:\n<code>{address}</code>\n\n"
            "💡 <b>Comment alimenter:</b>\n"
            "1️⃣ Achetez <b>USDC</b> sur un exchange (Binance, Bybit, Kraken)\n"
            "2️⃣ Retirez vers le réseau <b>Polygon (MATIC)</b> — pas Ethereum!\n"
            "3️⃣ Utilisez l'adresse ci-dessus\n"
            "4️⃣ Généralement 5-15 minutes — fonds reçus\n\n"
            "⚠️ <b>Réseau Polygon uniquement.</b> Ethereum ne fonctionnera pas — fonds perdus!\n\n"
            "🤖 <b>Activez AutoTrade</b> — l'algorithme trade pour vous 24/7. Seulement 20% des profits."
        ),
        "de": (
            "✅ <b>Wallet erstellt!</b>\n\n"
            "📋 Adresse:\n<code>{address}</code>\n\n"
            "💡 <b>Wie aufladen:</b>\n"
            "1️⃣ Kaufen Sie <b>USDC</b> auf einer Börse (Binance, Bybit, Kraken)\n"
            "2️⃣ Abheben an das <b>Polygon (MATIC)</b>-Netzwerk — nicht Ethereum!\n"
            "3️⃣ Verwenden Sie die obige Adresse\n"
            "4️⃣ Normalerweise 5-15 Minuten — Guthaben eingetroffen\n\n"
            "⚠️ <b>Nur Polygon-Netzwerk.</b> Ethereum funktioniert nicht — Geld geht verloren!\n\n"
            "🤖 <b>AutoTrade aktivieren</b> — der Algorithmus handelt 24/7 für Sie. Nur 20% vom Gewinn."
        ),
        "hi": (
            "✅ <b>वॉलेट बनाया गया!</b>\n\n"
            "📋 पता:\n<code>{address}</code>\n\n"
            "💡 <b>फंड कैसे करें:</b>\n"
            "1️⃣ एक्सचेंज पर <b>USDC</b> खरीदें (Binance, Bybit, Kraken)\n"
            "2️⃣ <b>Polygon (MATIC)</b> नेटवर्क पर निकालें — Ethereum नहीं!\n"
            "3️⃣ ऊपर दिए पते का उपयोग करें\n"
            "4️⃣ आमतौर पर 5-15 मिनट — फंड आ जाते हैं\n\n"
            "⚠️ <b>केवल Polygon नेटवर्क।</b> Ethereum काम नहीं करेगा — पैसे खो जाएंगे!\n\n"
            "🤖 <b>AutoTrade चालू करें</b> — एल्गोरिथम 24/7 आपके लिए ट्रेड करता है। केवल लाभ से 20%।"
        ),
        "ja": (
            "✅ <b>ウォレットが作成されました！</b>\n\n"
            "📋 アドレス：\n<code>{address}</code>\n\n"
            "💡 <b>入金方法：</b>\n"
            "1️⃣ 取引所で <b>USDC</b> を購入（Binance, Bybit, Kraken）\n"
            "2️⃣ <b>Polygon (MATIC)</b> ネットワークに出金 — Ethereumではない！\n"
            "3️⃣ 上記のアドレスを使用\n"
            "4️⃣ 通常5〜15分 — 資金が届く\n\n"
            "⚠️ <b>Polygonネットワークのみ。</b>Ethereumは使えません — 資金が失われます！\n\n"
            "🤖 <b>AutoTradeを有効化</b> — アルゴリズムが24時間自動取引。利益からの20%のみ。"
        ),
    },
    "wallet_exists": {
        "ru": (
            "✅ <b>Ваш кошелёк</b>\n\n"
            "📋 Адрес:\n<code>{address}</code>\n\n"
            "Пополни через биржу (Polygon USDC) и включай AutoTrade!"
        ),
        "en": (
            "✅ <b>Your Wallet</b>\n\n"
            "📋 Address:\n<code>{address}</code>\n\n"
            "Fund via exchange (Polygon USDC) and enable AutoTrade!"
        ),
    },
    "create_failed": {
        "ru": (
            "😔 Не удалось создать кошелёк автоматически.\n\n"
            "Это может быть временная проблема с Polymarket.\n"
            "Попробуй подключить свой кошелёк вручную или повтори позже."
        ),
        "en": (
            "😔 Could not create wallet automatically.\n\n"
            "This may be a temporary Polymarket issue.\n"
            "Try connecting your wallet manually or try again later."
        ),
    },
    "enter_address": {
        "ru": "Отправь адрес кошелька (начинается с 0x...):\n\nПример: <code>0x1234...abcd</code>",
        "en": "Send your wallet address (starts with 0x...):\n\nExample: <code>0x1234...abcd</code>",
    },
    "invalid_address": {
        "ru": "❌ Неверный адрес. Должен начинаться с 0x и содержать 42 символа. Попробуй снова:",
        "en": "❌ Invalid address. Must start with 0x and be 42 characters. Try again:",
    },
    "btn_create": {
        "ru": "🚀 Создать кошелёк", "en": "🚀 Create Wallet",
        "es": "🚀 Crear Cartera", "pt": "🚀 Criar Carteira",
        "tr": "🚀 Cüzdan Oluştur", "id": "🚀 Buat Dompet",
        "zh": "🚀 创建钱包", "ar": "🚀 إنشاء محفظة",
        "fr": "🚀 Créer Portefeuille", "de": "🚀 Wallet Erstellen",
        "hi": "🚀 वॉलेट बनाएं", "ja": "🚀 ウォレット作成",
    },
    "btn_connect": {
        "ru": "📲 Подключить свой", "en": "📲 Connect Existing",
        "es": "📲 Conectar Existente", "pt": "📲 Conectar Existente",
        "tr": "📲 Mevcut Bağla", "id": "📲 Hubungkan Ada",
        "zh": "📲 连接现有", "ar": "📲 ربط موجودة",
        "fr": "📲 Connecter Existant", "de": "📲 Vorhandene Verbinden",
        "hi": "📲 मौजूदा कनेक्ट", "ja": "📲 既存を接続",
    },
    "btn_back": {
        "ru": "🔙 Назад", "en": "🔙 Back",
        "es": "🔙 Atrás", "pt": "🔙 Voltar",
        "tr": "🔙 Geri", "id": "🔙 Kembali",
        "zh": "🔙 返回", "ar": "🔙 رجوع",
        "fr": "🔙 Retour", "de": "🔙 Zurück",
        "hi": "🔙 वापस", "ja": "🔙 戻る",
    },
    "btn_change": {
        "ru": "📝 Изменить", "en": "📝 Change",
        "es": "📝 Cambiar", "pt": "📝 Alterar",
        "tr": "📝 Değiştir", "id": "📝 Ubah",
        "zh": "📝 更改", "ar": "📝 تغيير",
        "fr": "📝 Modifier", "de": "📝 Ändern",
        "hi": "📝 बदलें", "ja": "📝 変更",
    },
}


def _t(key: str, lang: str) -> str:
    """Get translated text, fallback to English."""
    return T[key].get(lang, T[key].get("en", ""))


# ══════════════════════════════════════════════════════════════════════
# Handlers
# ══════════════════════════════════════════════════════════════════════

async def cmd_wallet(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handler for /wallet command or 💳 Wallet button."""
    user = await get_user(update.effective_user.id)
    lang = (user or {}).get("language", "ru")
    wallet = (user or {}).get("wallet_address")

    title = _t("wallet_title", lang)

    if wallet:
        text = title + "\n\n" + _t("wallet_exists", lang).format(address=wallet)
        keyboard = [
            [InlineKeyboardButton(_t("btn_change", lang), callback_data="wallet:add")],
            [InlineKeyboardButton(_t("btn_back", lang), callback_data="menu:main")],
        ]
    else:
        text = title + "\n\n" + _t("no_wallet", lang)
        keyboard = [
            [InlineKeyboardButton(_t("btn_create", lang), callback_data="wallet:create")],
            [InlineKeyboardButton(_t("btn_connect", lang), callback_data="wallet:add")],
            [InlineKeyboardButton(_t("btn_back", lang), callback_data="menu:main")],
        ]

    if update.message:
        await update.message.reply_html(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text, parse_mode="HTML",
                                      reply_markup=InlineKeyboardMarkup(keyboard))


async def cb_wallet_create(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    Автоматически создать кошелёк через Polymarket Relayer API.
    Генерируем EOA keypair, деплоим Safe, сохраняем всё в БД.
    """
    query = update.callback_query
    await query.answer()
    user = await get_user(query.from_user.id)
    lang = (user or {}).get("language", "ru")

    # Показываем индикатор загрузки
    await query.edit_message_text(_t("creating_wallet", lang), parse_mode="HTML")

    try:
        # Генерируем новый Ethereum keypair для пользователя
        from eth_account import Account
        acct = Account.create()
        signer_address = acct.address
        private_key    = acct.key.hex()

        # Деплоим Safe через Polymarket Relayer
        safe_address = await relayer.create_wallet(signer_address)

        if safe_address:
            # Сохраняем safe_address + signer + private_key в БД
            await save_generated_wallet(
                user_id        = query.from_user.id,
                wallet_address = safe_address,
                signer_address = signer_address,
                private_key    = private_key,
            )
            # Автоматически одобряем USDC для этого кошелька
            try:
                approve_ok = await relayer.approve_usdc(safe_address)
                if approve_ok:
                    print(f"[Wallet] USDC approved for {safe_address}")
                else:
                    print(f"[Wallet] USDC approve for {safe_address} returned False")
            except Exception as e:
                print(f"[Wallet] Warning: could not approve USDC for {safe_address}: {e}")
            text = _t("wallet_created", lang).format(address=safe_address)
        else:
            # Relayer недоступен — используем EOA напрямую
            await save_generated_wallet(
                user_id        = query.from_user.id,
                wallet_address = signer_address,
                signer_address = signer_address,
                private_key    = private_key,
            )
            # Пытаемся одобрить USDC и для EOA
            try:
                approve_ok = await relayer.approve_usdc(signer_address)
                if approve_ok:
                    print(f"[Wallet] USDC approved for {signer_address}")
                else:
                    print(f"[Wallet] USDC approve for {signer_address} returned False")
            except Exception as e:
                print(f"[Wallet] Warning: could not approve USDC for {signer_address}: {e}")
            text = _t("wallet_created", lang).format(address=signer_address)

    except ImportError:
        # eth_account не установлен — fallback на ручной ввод
        text = _t("create_failed", lang) + \
               ("\n\nПодключи кошелёк вручную 👇" if lang == "ru" else "\n\nConnect wallet manually 👇")
        keyboard = [
            [InlineKeyboardButton(_t("btn_connect", lang), callback_data="wallet:add")],
            [InlineKeyboardButton(_t("btn_back", lang), callback_data="menu:main")],
        ]
        await query.edit_message_text(text, parse_mode="HTML",
                                      reply_markup=InlineKeyboardMarkup(keyboard))
        return
    except Exception as e:
        print(f"[Wallet] Ошибка создания кошелька: {e}")
        text = _t("create_failed", lang)
        keyboard = [
            [InlineKeyboardButton(_t("btn_connect", lang), callback_data="wallet:add")],
            [InlineKeyboardButton(_t("btn_back", lang), callback_data="menu:main")],
        ]
        await query.edit_message_text(text, parse_mode="HTML",
                                      reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # Если пользователь шёл из Intel — вернуть к сигналу
    return_to = ctx.user_data.pop("return_after_wallet", None)
    if return_to:
        back_label = "⚡ " + ("К сигналу" if lang == "ru" else "Back to signal")
        keyboard = [
            [InlineKeyboardButton(back_label, callback_data=return_to)],
            [InlineKeyboardButton(_t("btn_back", lang), callback_data="menu:main")],
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("🤖 " + ("Включить AutoTrade" if lang == "ru" else "Enable AutoTrade"),
                                  callback_data="copy:menu")],
            [InlineKeyboardButton(_t("btn_back", lang), callback_data="menu:main")],
        ]
    await query.edit_message_text(text, parse_mode="HTML",
                                  reply_markup=InlineKeyboardMarkup(keyboard))


async def cb_wallet_add(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Начать ручной ввод адреса кошелька."""
    query = update.callback_query
    await query.answer()
    user = await get_user(query.from_user.id)
    lang = (user or {}).get("language", "ru")

    text = _t("enter_address", lang)
    keyboard = [[
        InlineKeyboardButton("❌ " + ("Отмена" if lang == "ru" else "Cancel"),
                             callback_data="wallet:cancel"),
    ]]
    await query.edit_message_text(text, parse_mode="HTML",
                                  reply_markup=InlineKeyboardMarkup(keyboard))
    ctx.user_data["wallet_lang"] = lang
    return WAIT_WALLET_ADDRESS


async def msg_wallet_address(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Получить адрес кошелька от пользователя."""
    address = update.message.text.strip()
    lang = ctx.user_data.get("wallet_lang", "ru")

    if not re.match(r"^0x[a-fA-F0-9]{40}$", address):
        await update.message.reply_html(_t("invalid_address", lang))
        return WAIT_WALLET_ADDRESS

    await update_user_wallet(update.effective_user.id, address)

    title = _t("wallet_title", lang)
    text = title + "\n\n" + _t("wallet_exists", lang).format(address=address)

    # Если пользователь шёл из Intel — вернуть к сигналу
    return_to = ctx.user_data.pop("return_after_wallet", None)
    if return_to:
        back_label = "⚡ " + ("К сигналу" if lang == "ru" else "Back to signal")
        keyboard = [
            [InlineKeyboardButton(back_label, callback_data=return_to)],
            [InlineKeyboardButton(_t("btn_back", lang), callback_data="menu:main")],
        ]
    else:
        keyboard = [[InlineKeyboardButton(_t("btn_back", lang), callback_data="menu:main")]]

    await update.message.reply_html(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END


async def cb_wallet_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Отмена ввода адреса."""
    query = update.callback_query
    await query.answer()
    ctx.user_data.pop("wallet_lang", None)
    await cmd_wallet(update, ctx)
    return ConversationHandler.END


async def cb_wallet_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Вернуться к статусу кошелька."""
    await cmd_wallet(update, ctx)


async def cb_wallet_guide(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Показать гайд (устаревший — теперь редирект на основной экран)."""
    await cmd_wallet(update, ctx)
