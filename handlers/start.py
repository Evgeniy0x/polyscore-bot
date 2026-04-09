# PolyScore — /start, /help, /language handlers (12 Languages, Premium Menu)

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.database import create_user, get_user, set_language


# ══════════════════════════════════════════════════════════════════════
# Тексты (RU / EN / ES / PT / TR / ID / ZH / AR / FR / DE / HI / JA)
# ══════════════════════════════════════════════════════════════════════

WELCOME = {
    "ru": (
        "⚡ <b>PolyScore — автоторговля на Polymarket</b>\n\n"
        "Зарабатывай на крупнейшем prediction market в мире\n"
        "($22B объёма в 2025 году).\n\n"
        "🤖 <b>AutoTrade</b> — бот торгует за тебя 24/7\n"
        "  Подключи кошелёк → алгоритм ищет прибыльные сделки\n"
        "  Ты видишь весь P&L в реальном времени\n"
        "  Мы берём 20% только с прибыли\n\n"
        "📊 <b>Торгуй сам</b>\n"
        "  ⚾ Спорт, крипта, политика, выборы\n"
        "  🎯 Парлеи, AI-прогнозы, алерты\n\n"
        "Выбери опцию ниже 👇"
    ),
    "en": (
        "⚡ <b>PolyScore — AutoTrading on Polymarket</b>\n\n"
        "Earn on the world's largest prediction market\n"
        "($22B volume in 2025).\n\n"
        "🤖 <b>AutoTrade</b> — bot trades for you 24/7\n"
        "  Connect wallet → algorithm finds profitable trades\n"
        "  Watch your P&L in real time\n"
        "  We take 20% only from profit\n\n"
        "📊 <b>Trade yourself</b>\n"
        "  ⚾ Sports, crypto, politics, elections\n"
        "  🎯 Parlays, AI picks, alerts\n\n"
        "Choose an option below 👇"
    ),
    "es": (
        "⚡ <b>PolyScore — AutoTrading en Polymarket</b>\n\n"
        "Gana en el mercado de predicción más grande del mundo\n"
        "($22B de volumen en 2025).\n\n"
        "🤖 <b>AutoTrade</b> — el bot opera por ti 24/7\n"
        "  Conecta tu cartera → el algoritmo encuentra operaciones rentables\n"
        "  Sigue tu P&L en tiempo real\n"
        "  Tomamos 20% solo de las ganancias\n\n"
        "📊 <b>Opera tú mismo</b>\n"
        "  ⚾ Deportes, cripto, política, elecciones\n"
        "  🎯 Parlays, selecciones IA, alertas\n\n"
        "Elige una opción a continuación 👇"
    ),
    "pt": (
        "⚡ <b>PolyScore — AutoTrading no Polymarket</b>\n\n"
        "Ganhe no maior mercado de previsão do mundo\n"
        "($22B de volume em 2025).\n\n"
        "🤖 <b>AutoTrade</b> — bot opera por você 24/7\n"
        "  Conecte a carteira → algoritmo encontra trades lucrativos\n"
        "  Acompanhe seu P&L em tempo real\n"
        "  Cobramos 20% apenas dos lucros\n\n"
        "📊 <b>Opere você mesmo</b>\n"
        "  ⚾ Esportes, cripto, política, eleições\n"
        "  🎯 Múltiplas, previsões IA, alertas\n\n"
        "Escolha uma opção abaixo 👇"
    ),
    "tr": (
        "⚡ <b>PolyScore — Polymarket'ta AutoTrading</b>\n\n"
        "Dünyanın en büyük tahmin piyasasında kazan\n"
        "(2025'te $22B hacim).\n\n"
        "🤖 <b>AutoTrade</b> — bot senin için 7/24 işlem yapar\n"
        "  Cüzdanı bağla → algoritma karlı işlemler bulur\n"
        "  P&L'ini gerçek zamanlı izle\n"
        "  Sadece kârdan %20 alıyoruz\n\n"
        "📊 <b>Kendin işlem yap</b>\n"
        "  ⚾ Spor, kripto, siyaset, seçimler\n"
        "  🎯 Kombineler, AI seçimleri, uyarılar\n\n"
        "Aşağıdan bir seçenek seçin 👇"
    ),
    "id": (
        "⚡ <b>PolyScore — AutoTrading di Polymarket</b>\n\n"
        "Hasilkan dari pasar prediksi terbesar di dunia\n"
        "(Volume $22B di 2025).\n\n"
        "🤖 <b>AutoTrade</b> — bot trading untuk Anda 24/7\n"
        "  Hubungkan dompet → algoritma cari trade menguntungkan\n"
        "  Pantau P&L Anda secara real time\n"
        "  Kami ambil 20% hanya dari profit\n\n"
        "📊 <b>Trading sendiri</b>\n"
        "  ⚾ Olahraga, kripto, politik, pemilu\n"
        "  🎯 Parlay, pilihan AI, peringatan\n\n"
        "Pilih opsi di bawah 👇"
    ),
    "zh": (
        "⚡ <b>PolyScore — Polymarket 自动交易</b>\n\n"
        "在全球最大预测市场赚钱\n"
        "（2025年交易量 $22B）。\n\n"
        "🤖 <b>AutoTrade</b> — 机器人24/7为您交易\n"
        "  连接钱包 → 算法寻找盈利交易机会\n"
        "  实时查看您的盈亏\n"
        "  我们只从利润中收取20%\n\n"
        "📊 <b>自己交易</b>\n"
        "  ⚾ 体育、加密货币、政治、选举\n"
        "  🎯 串关、AI预测、提醒\n\n"
        "选择下面的选项 👇"
    ),
    "ar": (
        "⚡ <b>PolyScore — التداول التلقائي على Polymarket</b>\n\n"
        "اكسب في أكبر سوق تنبؤ في العالم\n"
        "(حجم $22B في 2025).\n\n"
        "🤖 <b>AutoTrade</b> — البوت يتداول نيابةً عنك 24/7\n"
        "  اربط المحفظة → الخوارزمية تجد صفقات مربحة\n"
        "  تابع أرباحك وخسائرك في الوقت الفعلي\n"
        "  نأخذ 20% فقط من الأرباح\n\n"
        "📊 <b>تداول بنفسك</b>\n"
        "  ⚾ رياضة، كريبتو، سياسة، انتخابات\n"
        "  🎯 رهانات مركبة، توقعات الذكاء الاصطناعي، تنبيهات\n\n"
        "اختر خيار أدناه 👇"
    ),
    "fr": (
        "⚡ <b>PolyScore — AutoTrading sur Polymarket</b>\n\n"
        "Gagnez sur le plus grand marché de prédiction au monde\n"
        "(Volume $22B en 2025).\n\n"
        "🤖 <b>AutoTrade</b> — le bot trade pour vous 24/7\n"
        "  Connectez votre portefeuille → l'algorithme trouve des trades rentables\n"
        "  Suivez votre P&L en temps réel\n"
        "  Nous prenons 20% uniquement sur les profits\n\n"
        "📊 <b>Tradez vous-même</b>\n"
        "  ⚾ Sports, crypto, politique, élections\n"
        "  🎯 Combinés, sélections IA, alertes\n\n"
        "Choisissez une option ci-dessous 👇"
    ),
    "de": (
        "⚡ <b>PolyScore — AutoTrading auf Polymarket</b>\n\n"
        "Verdiene am größten Vorhersagemarkt der Welt\n"
        "(Volume $22B in 2025).\n\n"
        "🤖 <b>AutoTrade</b> — Bot handelt 24/7 für dich\n"
        "  Wallet verbinden → Algorithmus findet profitable Trades\n"
        "  P&L in Echtzeit verfolgen\n"
        "  Wir nehmen nur 20% vom Gewinn\n\n"
        "📊 <b>Selbst traden</b>\n"
        "  ⚾ Sport, Krypto, Politik, Wahlen\n"
        "  🎯 Mehrfachwetten, KI-Picks, Benachrichtigungen\n\n"
        "Wähle eine Option unten 👇"
    ),
    "hi": (
        "⚡ <b>PolyScore — Polymarket पर AutoTrading</b>\n\n"
        "दुनिया के सबसे बड़े प्रेडिक्शन मार्केट में कमाएं\n"
        "(2025 में $22B वॉल्यूम)।\n\n"
        "🤖 <b>AutoTrade</b> — बॉट आपके लिए 24/7 ट्रेड करता है\n"
        "  वॉलेट जोड़ें → एल्गोरिदम लाभदायक ट्रेड खोजता है\n"
        "  रियल टाइम में P&L देखें\n"
        "  हम केवल मुनाफे से 20% लेते हैं\n\n"
        "📊 <b>खुद ट्रेड करें</b>\n"
        "  ⚾ खेल, क्रिप्टो, राजनीति, चुनाव\n"
        "  🎯 परले, AI पिक्स, अलर्ट\n\n"
        "नीचे एक विकल्प चुनें 👇"
    ),
    "ja": (
        "⚡ <b>PolyScore — Polymarketで自動取引</b>\n\n"
        "世界最大の予測マーケットで稼ぐ\n"
        "（2025年取引高 $22B）。\n\n"
        "🤖 <b>AutoTrade</b> — ボットが24/7あなたの代わりに取引\n"
        "  ウォレット接続 → アルゴリズムが利益のある取引を検索\n"
        "  リアルタイムでP&Lを確認\n"
        "  利益の20%のみいただきます\n\n"
        "📊 <b>自分でトレード</b>\n"
        "  ⚾ スポーツ、クリプト、政治、選挙\n"
        "  🎯 パーレイ、AIピック、アラート\n\n"
        "下のオプションを選択してください 👇"
    ),
}

# ── Main Menu  (v2 — focused, action-first, 4 rows max) ───────────────
# Row 1: Intel Feed  (primary CTA — live signals)
# Row 2: Trade / Trending
# Row 3: Portfolio / Wallet
# Row 4: More (parlay, alerts, settings, academy) — collapsed into 2 buttons
#
# Removed from primary: leaderboard, AI morning briefing (still accessible via /ai)
# Academy hidden in ⚙️ More menu — accessible but not cluttering home
# ──────────────────────────────────────────────────────────────────────

def _make_main_menu(lang: str) -> list:
    """Generate a focused 4-row main menu for given language."""
    # Row 1 — Intel Feed: the main value proposition
    intel_labels = {
        "ru": "🧠 Intel Feed — живые сигналы",
        "en": "🧠 Intel Feed — live signals",
        "es": "🧠 Intel Feed — señales en vivo",
        "pt": "🧠 Intel Feed — sinais ao vivo",
        "tr": "🧠 Intel Feed — canlı sinyaller",
        "id": "🧠 Intel Feed — sinyal langsung",
        "zh": "🧠 Intel Feed — 实时信号",
        "ar": "🧠 Intel Feed — إشارات مباشرة",
        "fr": "🧠 Intel Feed — signaux en direct",
        "de": "🧠 Intel Feed — Live-Signale",
        "hi": "🧠 Intel Feed — लाइव सिग्नल",
        "ja": "🧠 Intel Feed — ライブシグナル",
    }

    # Row 2 — AutoTrade full-width
    autotrade_labels = {
        "ru": "🤖 AutoTrade — бот торгует за меня 24/7",
        "en": "🤖 AutoTrade — bot trades for me 24/7",
        "es": "🤖 AutoTrade — el bot opera por mí 24/7",
        "pt": "🤖 AutoTrade — bot opera por mim 24/7",
        "tr": "🤖 AutoTrade — bot benim için 24/7 işlem yapar",
        "id": "🤖 AutoTrade — bot trading untuk saya 24/7",
        "zh": "🤖 AutoTrade — 机器人替我24/7交易",
        "ar": "🤖 AutoTrade — البوت يتداول عني 24/7",
        "fr": "🤖 AutoTrade — le bot trade pour moi 24/7",
        "de": "🤖 AutoTrade — Bot handelt 24/7 für mich",
        "hi": "🤖 AutoTrade — बॉट मेरे लिए 24/7 ट्रेड करे",
        "ja": "🤖 AutoTrade — ボットが24/7取引",
    }

    # Row 3 — Markets / Portfolio
    trade_labels  = {"ru": "📈 Рынки", "en": "📈 Markets", "es": "📈 Mercados",
                     "pt": "📈 Mercados", "tr": "📈 Pazarlar", "id": "📈 Pasar",
                     "zh": "📈 市场", "ar": "📈 الأسواق", "fr": "📈 Marchés",
                     "de": "📈 Märkte", "hi": "📈 बाजार", "ja": "📈 マーケット"}
    port_labels   = {"ru": "📊 Портфель", "en": "📊 Portfolio", "es": "📊 Posiciones",
                     "pt": "📊 Portfólio", "tr": "📊 Portföy", "id": "📊 Portofolio",
                     "zh": "📊 持仓", "ar": "📊 محفظتي", "fr": "📊 Portefeuille",
                     "de": "📊 Portfolio", "hi": "📊 पोर्टफोलियो", "ja": "📊 ポートフォリオ"}

    # Row 4 — Wallet / Settings
    wallet_labels = {"ru": "💳 Кошелёк", "en": "💳 Wallet", "es": "💳 Cartera",
                     "pt": "💳 Carteira", "tr": "💳 Cüzdan", "id": "💳 Dompet",
                     "zh": "💳 钱包", "ar": "💳 المحفظة", "fr": "💳 Portefeuille",
                     "de": "💳 Wallet", "hi": "💳 वॉलेट", "ja": "💳 ウォレット"}
    settings_labels = {"ru": "⚙️ Ещё", "en": "⚙️ More", "es": "⚙️ Más",
                       "pt": "⚙️ Mais", "tr": "⚙️ Daha", "id": "⚙️ Lagi",
                       "zh": "⚙️ 更多", "ar": "⚙️ المزيد", "fr": "⚙️ Plus",
                       "de": "⚙️ Mehr", "hi": "⚙️ और", "ja": "⚙️ もっと"}

    # Trending labels (заменяет Intel Feed — прямой доступ к горячим рынкам)
    trending_labels = {
        "ru": "🔥 Горячие рынки", "en": "🔥 Trending Markets",
        "es": "🔥 Mercados Calientes", "pt": "🔥 Mercados Quentes",
        "tr": "🔥 Trend Pazarlar", "id": "🔥 Pasar Trending",
        "zh": "🔥 热门市场", "ar": "🔥 الأسواق الرائجة",
        "fr": "🔥 Marchés Tendance", "de": "🔥 Trending Märkte",
        "hi": "🔥 ट्रेंडिंग मार्केट", "ja": "🔥 トレンドマーケット",
    }

    l = lang if lang in trending_labels else "en"
    return [
        [InlineKeyboardButton(trending_labels.get(l, "🔥 Trending Markets"), callback_data="cat:trending")],
        [InlineKeyboardButton(autotrade_labels[l], callback_data="copy:menu")],
        [InlineKeyboardButton(trade_labels.get(l, "📈 Markets"),    callback_data="cat:markets"),
         InlineKeyboardButton(port_labels.get(l, "📊 Portfolio"),   callback_data="portfolio")],
        [InlineKeyboardButton(wallet_labels.get(l, "💳 Wallet"),    callback_data="wallet:status"),
         InlineKeyboardButton(settings_labels.get(l, "⚙️ More"),    callback_data="settings")],
    ]


# Build MAIN_MENU dict from function (keeps backward compat with imports)
MAIN_MENU = {lang: _make_main_menu(lang) for lang in [
    "ru", "en", "es", "pt", "tr", "id", "zh", "ar", "fr", "de", "hi", "ja"
]}

# Language flags and names for selection (3x4 grid)
LANGUAGE_FLAGS = {
    "ru": "🇷🇺",
    "en": "🇬🇧",
    "es": "🇪🇸",
    "pt": "🇵🇹",
    "tr": "🇹🇷",
    "id": "🇮🇩",
    "zh": "🇨🇳",
    "ar": "🇸🇦",
    "fr": "🇫🇷",
    "de": "🇩🇪",
    "hi": "🇮🇳",
    "ja": "🇯🇵",
}

LANGUAGE_NAMES = {
    "ru": "Русский",
    "en": "English",
    "es": "Español",
    "pt": "Português",
    "tr": "Türkçe",
    "id": "Bahasa Indonesia",
    "zh": "中文",
    "ar": "العربية",
    "fr": "Français",
    "de": "Deutsch",
    "hi": "हिन्दी",
    "ja": "日本語",
}

HELP_TEXTS = {
    "ru": (
        "📖 <b>Команды PolyScore</b>\n\n"
        "/start — главное меню\n"
        "/sports — рынки (спорт, крипта, политика)\n"
        "/trending — горячие рынки\n"
        "/portfolio — мои позиции\n"
        "/ai — AI-брифинг\n"
        "/lang — выбрать язык\n"
        "/wallet — кошелёк\n\n"
        "🤖 AutoTrade — алгоритм торгует 24/7\n"
        "💰 20% только с прибыли\n\n"
        "📩 Поддержка: @PolyScoreSupport"
    ),
    "en": (
        "📖 <b>PolyScore Commands</b>\n\n"
        "/start — main menu\n"
        "/sports — markets (sports, crypto, politics)\n"
        "/trending — hot markets\n"
        "/portfolio — my positions\n"
        "/ai — AI briefing\n"
        "/lang — select language\n"
        "/wallet — wallet\n\n"
        "🤖 AutoTrade — algorithm trades 24/7\n"
        "💰 20% only from profit\n\n"
        "📩 Support: @PolyScoreSupport"
    ),
    "es": (
        "📖 <b>Comandos de PolyScore</b>\n\n"
        "/start — menú principal\n"
        "/sports — mercados (deportes, cripto, política)\n"
        "/trending — mercados calientes\n"
        "/portfolio — mis posiciones\n"
        "/ai — resumen IA\n"
        "/lang — seleccionar idioma\n"
        "/wallet — billetera\n\n"
        "🤖 AutoTrade — algoritmo opera 24/7\n"
        "💰 Solo 20% de las ganancias\n\n"
        "📩 Soporte: @PolyScoreSupport"
    ),
    "pt": (
        "📖 <b>Comandos do PolyScore</b>\n\n"
        "/start — menu principal\n"
        "/sports — mercados (esportes, cripto, política)\n"
        "/trending — mercados quentes\n"
        "/portfolio — minhas posições\n"
        "/ai — briefing IA\n"
        "/lang — selecionar idioma\n"
        "/wallet — carteira\n\n"
        "🤖 AutoTrade — algoritmo opera 24/7\n"
        "💰 Apenas 20% dos lucros\n\n"
        "📩 Suporte: @PolyScoreSupport"
    ),
    "tr": (
        "📖 <b>PolyScore Komutları</b>\n\n"
        "/start — ana menü\n"
        "/sports — piyasalar (spor, kripto, siyaset)\n"
        "/trending — sıcak piyasalar\n"
        "/portfolio — pozisyonlarım\n"
        "/ai — AI özeti\n"
        "/lang — dil seç\n"
        "/wallet — cüzdan\n\n"
        "🤖 AutoTrade — algoritma 7/24 işlem yapar\n"
        "💰 Sadece kârdan %20\n\n"
        "📩 Destek: @PolyScoreSupport"
    ),
    "id": (
        "📖 <b>Perintah PolyScore</b>\n\n"
        "/start — menu utama\n"
        "/sports — pasar (olahraga, kripto, politik)\n"
        "/trending — pasar trending\n"
        "/portfolio — posisi saya\n"
        "/ai — ringkasan AI\n"
        "/lang — pilih bahasa\n"
        "/wallet — dompet\n\n"
        "🤖 AutoTrade — algoritma trading 24/7\n"
        "💰 Hanya 20% dari profit\n\n"
        "📩 Dukungan: @PolyScoreSupport"
    ),
    "zh": (
        "📖 <b>PolyScore 命令</b>\n\n"
        "/start — 主菜单\n"
        "/sports — 市场（体育、加密、政治）\n"
        "/trending — 热门市场\n"
        "/portfolio — 我的持仓\n"
        "/ai — AI摘要\n"
        "/lang — 选择语言\n"
        "/wallet — 钱包\n\n"
        "🤖 AutoTrade — 算法24/7自动交易\n"
        "💰 仅从利润中收取20%\n\n"
        "📩 支持: @PolyScoreSupport"
    ),
    "ar": (
        "📖 <b>أوامر PolyScore</b>\n\n"
        "/start — القائمة الرئيسية\n"
        "/sports — الأسواق (رياضة، كريبتو، سياسة)\n"
        "/trending — الأسواق الشعبية\n"
        "/portfolio — مراكزي\n"
        "/ai — ملخص AI\n"
        "/lang — اختر اللغة\n"
        "/wallet — المحفظة\n\n"
        "🤖 AutoTrade — الخوارزمية تتداول 24/7\n"
        "💰 فقط 20% من الأرباح\n\n"
        "📩 الدعم: @PolyScoreSupport"
    ),
    "fr": (
        "📖 <b>Commandes PolyScore</b>\n\n"
        "/start — menu principal\n"
        "/sports — marchés (sports, crypto, politique)\n"
        "/trending — marchés populaires\n"
        "/portfolio — mes positions\n"
        "/ai — résumé IA\n"
        "/lang — sélectionner la langue\n"
        "/wallet — portefeuille\n\n"
        "🤖 AutoTrade — l'algorithme trade 24/7\n"
        "💰 Seulement 20% des profits\n\n"
        "📩 Support: @PolyScoreSupport"
    ),
    "de": (
        "📖 <b>PolyScore-Befehle</b>\n\n"
        "/start — Hauptmenü\n"
        "/sports — Märkte (Sport, Krypto, Politik)\n"
        "/trending — Beliebte Märkte\n"
        "/portfolio — meine Positionen\n"
        "/ai — KI-Zusammenfassung\n"
        "/lang — Sprache wählen\n"
        "/wallet — Wallet\n\n"
        "🤖 AutoTrade — Algorithmus handelt 24/7\n"
        "💰 Nur 20% vom Gewinn\n\n"
        "📩 Support: @PolyScoreSupport"
    ),
    "hi": (
        "📖 <b>PolyScore कमांड</b>\n\n"
        "/start — मुख्य मेनू\n"
        "/sports — बाजार (खेल, क्रिप्टो, राजनीति)\n"
        "/trending — लोकप्रिय बाजार\n"
        "/portfolio — मेरी पोजीशन\n"
        "/ai — AI ब्रीफिंग\n"
        "/lang — भाषा चुनें\n"
        "/wallet — वॉलेट\n\n"
        "🤖 AutoTrade — एल्गोरिथम 24/7 ट्रेड करता है\n"
        "💰 केवल लाभ से 20%\n\n"
        "📩 समर्थन: @PolyScoreSupport"
    ),
    "ja": (
        "📖 <b>PolyScore コマンド</b>\n\n"
        "/start — メインメニュー\n"
        "/sports — マーケット（スポーツ、クリプト、政治）\n"
        "/trending — ホットマーケット\n"
        "/portfolio — 私のポジション\n"
        "/ai — AI要約\n"
        "/lang — 言語を選択\n"
        "/wallet — ウォレット\n\n"
        "🤖 AutoTrade — アルゴリズムが24時間取引\n"
        "💰 利益の20%のみ\n\n"
        "📩 サポート: @PolyScoreSupport"
    ),
}

LANGUAGE_CHANGED = {
    "ru": "✅ Язык изменён на русский.",
    "en": "✅ Language changed to English.",
    "es": "✅ Idioma cambiado a español.",
    "pt": "✅ Idioma alterado para português.",
    "tr": "✅ Dil Türkçeye değiştirildi.",
    "id": "✅ Bahasa diubah ke Indonesia.",
    "zh": "✅ 语言已更改为中文。",
    "ar": "✅ تم تغيير اللغة إلى العربية.",
    "fr": "✅ Langue changée en français.",
    "de": "✅ Sprache zu Deutsch geändert.",
    "hi": "✅ भाषा हिंदी में बदल दी गई है।",
    "ja": "✅ 言語が日本語に変更されました。",
}


def _get_user_language(user_tg_language_code: str) -> str:
    """Auto-detect language from Telegram user's language_code."""
    if not user_tg_language_code:
        return "en"

    # Handle language variants
    lang_base = user_tg_language_code.lower().split("-")[0]

    mapping = {
        "ru": "ru",
        "en": "en",
        "es": "es",
        "pt": "pt",
        "tr": "tr",
        "id": "id",
        "zh": "zh",
        "ar": "ar",
        "fr": "fr",
        "de": "de",
        "hi": "hi",
        "ja": "ja",
    }
    return mapping.get(lang_base, "en")


ONBOARDING = {
    "ru": (
        "👋 <b>Добро пожаловать в PolyScore!</b>\n\n"
        "Автоматическая торговля на <b>Polymarket</b> — прямо в Telegram.\n\n"
        "Чтобы начать:\n"
        "1. Создай кошелёк Polygon — займёт 5 секунд\n"
        "2. Пополни <b>USDC</b> в сети <b>Polygon</b>\n"
        "3. Включи AutoTrade — алгоритм торгует за тебя 24/7\n\n"
        "🔐 <b>Безопасность.</b> Ключ хранится в зашифрованном виде (AES-256).\n"
        "Или подключи свой кошелёк — тогда мы вообще не знаем твой ключ.\n\n"
        "💰 <b>20% только с прибыли.</b> Нет прибыли — нет комиссии."
    ),
    "en": (
        "👋 <b>Welcome to PolyScore!</b>\n\n"
        "Automated trading on <b>Polymarket</b> — right inside Telegram.\n\n"
        "To start:\n"
        "1. Create a Polygon wallet — takes 5 seconds\n"
        "2. Fund it with <b>USDC</b> on <b>Polygon</b> network\n"
        "3. Enable AutoTrade — algorithm trades for you 24/7\n\n"
        "🔐 <b>Security.</b> Your key is stored encrypted (AES-256).\n"
        "Or connect your own wallet — we never see your key.\n\n"
        "💰 <b>20% only from profit.</b> No profit — no fee."
    ),
    "es": (
        "👋 <b>¡Bienvenido a PolyScore!</b>\n\n"
        "Trading automático en <b>Polymarket</b> — directamente en Telegram.\n\n"
        "Para empezar:\n"
        "1. Crea una billetera Polygon — tarda 5 segundos\n"
        "2. Recárgala con <b>USDC</b> en la red <b>Polygon</b>\n"
        "3. Activa AutoTrade — el algoritmo opera por ti 24/7\n\n"
        "💰 <b>Solo 20% de las ganancias.</b> Sin ganancia — sin comisión."
    ),
    "pt": (
        "👋 <b>Bem-vindo ao PolyScore!</b>\n\n"
        "Trading automático no <b>Polymarket</b> — direto no Telegram.\n\n"
        "Para começar:\n"
        "1. Crie uma carteira Polygon — leva 5 segundos\n"
        "2. Recarregue com <b>USDC</b> na rede <b>Polygon</b>\n"
        "3. Ative o AutoTrade — algoritmo opera por você 24/7\n\n"
        "💰 <b>Apenas 20% dos lucros.</b> Sem lucro — sem taxa."
    ),
    "tr": (
        "👋 <b>PolyScore'a Hoş Geldin!</b>\n\n"
        "<b>Polymarket</b>'te otomatik trading — doğrudan Telegram'da.\n\n"
        "Başlamak için:\n"
        "1. Polygon cüzdanı oluştur — 5 saniye sürer\n"
        "2. <b>Polygon</b> ağında <b>USDC</b> ile doldur\n"
        "3. AutoTrade'i etkinleştir — algoritma 7/24 senin için işlem yapar\n\n"
        "💰 <b>Sadece kârdan %20.</b> Kâr yok — komisyon yok."
    ),
    "id": (
        "👋 <b>Selamat Datang di PolyScore!</b>\n\n"
        "Trading otomatis di <b>Polymarket</b> — langsung di Telegram.\n\n"
        "Untuk memulai:\n"
        "1. Buat dompet Polygon — hanya 5 detik\n"
        "2. Isi dengan <b>USDC</b> di jaringan <b>Polygon</b>\n"
        "3. Aktifkan AutoTrade — algoritma trading untuk Anda 24/7\n\n"
        "💰 <b>Hanya 20% dari profit.</b> Tidak ada profit — tidak ada biaya."
    ),
    "zh": (
        "👋 <b>欢迎来到 PolyScore!</b>\n\n"
        "在 <b>Polymarket</b> 上自动交易 — 直接在 Telegram 中。\n\n"
        "开始步骤：\n"
        "1. 创建 Polygon 钱包 — 只需5秒\n"
        "2. 在 <b>Polygon</b> 网络充值 <b>USDC</b>\n"
        "3. 开启 AutoTrade — 算法24/7为您交易\n\n"
        "💰 <b>仅从利润中收取20%。</b>没有利润 — 没有费用。"
    ),
    "ar": (
        "👋 <b>مرحباً بك في PolyScore!</b>\n\n"
        "تداول آلي على <b>Polymarket</b> — مباشرة في Telegram.\n\n"
        "للبدء:\n"
        "1. أنشئ محفظة Polygon — تستغرق 5 ثوانٍ\n"
        "2. موّلها بـ <b>USDC</b> على شبكة <b>Polygon</b>\n"
        "3. فعّل AutoTrade — الخوارزمية تتداول لك 24/7\n\n"
        "💰 <b>فقط 20% من الأرباح.</b> لا أرباح — لا عمولة."
    ),
    "fr": (
        "👋 <b>Bienvenue sur PolyScore!</b>\n\n"
        "Trading automatique sur <b>Polymarket</b> — directement dans Telegram.\n\n"
        "Pour commencer:\n"
        "1. Crée un portefeuille Polygon — 5 secondes\n"
        "2. Recharge en <b>USDC</b> sur le réseau <b>Polygon</b>\n"
        "3. Active AutoTrade — l'algorithme trade pour toi 24/7\n\n"
        "💰 <b>Seulement 20% des profits.</b> Pas de profit — pas de frais."
    ),
    "de": (
        "👋 <b>Willkommen bei PolyScore!</b>\n\n"
        "Automatisches Trading auf <b>Polymarket</b> — direkt in Telegram.\n\n"
        "So startest du:\n"
        "1. Erstelle eine Polygon Wallet — dauert 5 Sekunden\n"
        "2. Mit <b>USDC</b> im <b>Polygon</b>-Netzwerk aufladen\n"
        "3. AutoTrade aktivieren — der Algorithmus handelt 24/7 für dich\n\n"
        "💰 <b>Nur 20% vom Gewinn.</b> Kein Gewinn — keine Gebühr."
    ),
    "hi": (
        "👋 <b>PolyScore में आपका स्वागत है!</b>\n\n"
        "<b>Polymarket</b> पर स्वचालित ट्रेडिंग — सीधे Telegram में।\n\n"
        "शुरू करने के लिए:\n"
        "1. Polygon वॉलेट बनाएं — 5 सेकंड\n"
        "2. <b>Polygon</b> नेटवर्क पर <b>USDC</b> से फंड करें\n"
        "3. AutoTrade चालू करें — एल्गोरिथम 24/7 आपके लिए ट्रेड करता है\n\n"
        "💰 <b>केवल लाभ से 20%।</b> कोई लाभ नहीं — कोई शुल्क नहीं।"
    ),
    "ja": (
        "👋 <b>PolyScoreへようこそ!</b>\n\n"
        "<b>Polymarket</b> での自動取引 — Telegram内で直接。\n\n"
        "始め方：\n"
        "1. Polygonウォレットを作成 — 5秒で完了\n"
        "2. <b>Polygon</b>ネットワークで <b>USDC</b> を入金\n"
        "3. AutoTradeを有効化 — アルゴリズムが24時間自動取引\n\n"
        "💰 <b>利益の20%のみ。</b>利益なし — 手数料なし。"
    ),
}

ONBOARDING_MENU = {
    lang: [
        [InlineKeyboardButton(
            "🚀 Создать кошелёк" if lang == "ru" else
            "🚀 Create Wallet" if lang == "en" else
            "🚀 Crear billetera" if lang == "es" else
            "🚀 Criar carteira" if lang == "pt" else
            "🚀 Cüzdan Oluştur" if lang == "tr" else
            "🚀 Buat Dompet" if lang == "id" else
            "🚀 创建钱包" if lang == "zh" else
            "🚀 إنشاء محفظة" if lang == "ar" else
            "🚀 Créer un portefeuille" if lang == "fr" else
            "🚀 Wallet erstellen" if lang == "de" else
            "🚀 वॉलेट बनाएं" if lang == "hi" else
            "🚀 ウォレット作成",
            callback_data="wallet:create"
        )],
        [InlineKeyboardButton(
            "📲 У меня уже есть кошелёк" if lang == "ru" else
            "📲 I already have a wallet" if lang == "en" else
            "📲 Ya tengo billetera" if lang == "es" else
            "📲 Já tenho carteira" if lang == "pt" else
            "📲 Zaten cüzdanım var" if lang == "tr" else
            "📲 Saya sudah punya dompet" if lang == "id" else
            "📲 我已有钱包" if lang == "zh" else
            "📲 لديّ محفظة بالفعل" if lang == "ar" else
            "📲 J'ai déjà un portefeuille" if lang == "fr" else
            "📲 Ich habe bereits eine Wallet" if lang == "de" else
            "📲 मेरे पास पहले से वॉलेट है" if lang == "hi" else
            "📲 すでにウォレットを持っています",
            callback_data="wallet:add"
        )],
        [InlineKeyboardButton(
            "👀 Сначала посмотреть рынки" if lang == "ru" else
            "👀 Browse markets first" if lang == "en" else
            "👀 Ver mercados primero" if lang == "es" else
            "👀 Ver mercados primeiro" if lang == "pt" else
            "👀 Önce piyasaları gör" if lang == "tr" else
            "👀 Lihat pasar dulu" if lang == "id" else
            "👀 先浏览市场" if lang == "zh" else
            "👀 تصفح الأسواق أولاً" if lang == "ar" else
            "👀 D'abord voir les marchés" if lang == "fr" else
            "👀 Erst Märkte ansehen" if lang == "de" else
            "👀 पहले बाजार देखें" if lang == "hi" else
            "👀 まず市場を見る",
            callback_data="menu:main"
        )],
    ]
    for lang in ["ru", "en", "es", "pt", "tr", "id", "zh", "ar", "fr", "de", "hi", "ja"]
}


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handler for /start — онбординг для новых, меню для старых."""
    user_tg = update.effective_user
    user    = await create_user(user_tg.id, user_tg.username or "")
    lang    = user.get("language")

    # Первый раз или язык не задан — авто-определяем
    if not lang:
        lang = _get_user_language(user_tg.language_code or "en")

    # Если у пользователя нет кошелька — показываем онбординг
    if not user.get("wallet_address"):
        await update.message.reply_html(
            ONBOARDING.get(lang, ONBOARDING["en"]),
            reply_markup=InlineKeyboardMarkup(ONBOARDING_MENU.get(lang, ONBOARDING_MENU["en"]))
        )
    else:
        # Уже есть кошелёк — показываем обычное меню
        await update.message.reply_html(
            WELCOME[lang],
            reply_markup=InlineKeyboardMarkup(MAIN_MENU[lang])
        )


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handler for /help — show commands in user's language."""
    user = await get_user(update.effective_user.id)
    lang = (user or {}).get("language")

    # Default to auto-detected language if not set
    if not lang:
        user_tg = update.effective_user
        lang = _get_user_language(user_tg.language_code or "en")

    text = HELP_TEXTS.get(lang, HELP_TEXTS["en"])
    await update.message.reply_html(text)


LANGUAGE_CODES = {"ru", "en", "es", "pt", "tr", "id", "zh", "ar", "fr", "de", "hi", "ja"}


async def cmd_language(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handler for /lang — show beautiful language picker with flags (3x4 grid)."""
    args = ctx.args
    user = await get_user(update.effective_user.id)
    lang = (user or {}).get("language")

    # Direct language setting via command (e.g., /lang es)
    if args and len(args) > 0 and args[0] in LANGUAGE_CODES:
        new_lang = args[0]
        await set_language(update.effective_user.id, new_lang)
        confirmation = LANGUAGE_CHANGED.get(new_lang, LANGUAGE_CHANGED["en"])
        await update.message.reply_text(confirmation)
    else:
        # Show beautiful 3x4 language picker grid
        if not lang:
            lang = _get_user_language(update.effective_user.language_code or "en")

        # 3-column grid layout (12 languages = 4 rows × 3 columns)
        buttons = [
            [
                InlineKeyboardButton(f"{LANGUAGE_FLAGS['ru']} {LANGUAGE_NAMES['ru']}", callback_data="lang:ru"),
                InlineKeyboardButton(f"{LANGUAGE_FLAGS['en']} {LANGUAGE_NAMES['en']}", callback_data="lang:en"),
                InlineKeyboardButton(f"{LANGUAGE_FLAGS['es']} {LANGUAGE_NAMES['es']}", callback_data="lang:es"),
            ],
            [
                InlineKeyboardButton(f"{LANGUAGE_FLAGS['pt']} {LANGUAGE_NAMES['pt']}", callback_data="lang:pt"),
                InlineKeyboardButton(f"{LANGUAGE_FLAGS['tr']} {LANGUAGE_NAMES['tr']}", callback_data="lang:tr"),
                InlineKeyboardButton(f"{LANGUAGE_FLAGS['id']} {LANGUAGE_NAMES['id']}", callback_data="lang:id"),
            ],
            [
                InlineKeyboardButton(f"{LANGUAGE_FLAGS['zh']} {LANGUAGE_NAMES['zh']}", callback_data="lang:zh"),
                InlineKeyboardButton(f"{LANGUAGE_FLAGS['ar']} {LANGUAGE_NAMES['ar']}", callback_data="lang:ar"),
                InlineKeyboardButton(f"{LANGUAGE_FLAGS['fr']} {LANGUAGE_NAMES['fr']}", callback_data="lang:fr"),
            ],
            [
                InlineKeyboardButton(f"{LANGUAGE_FLAGS['de']} {LANGUAGE_NAMES['de']}", callback_data="lang:de"),
                InlineKeyboardButton(f"{LANGUAGE_FLAGS['hi']} {LANGUAGE_NAMES['hi']}", callback_data="lang:hi"),
                InlineKeyboardButton(f"{LANGUAGE_FLAGS['ja']} {LANGUAGE_NAMES['ja']}", callback_data="lang:ja"),
            ],
        ]

        await update.message.reply_html(
            "🌍 <b>Select your language / Выберите язык</b>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )


async def cb_language(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Callback for lang:* — set user language and show main menu."""
    query = update.callback_query
    await query.answer()
    lang = query.data.split(":")[1]

    if lang not in LANGUAGE_CODES:
        await query.edit_message_text("❌ Invalid language")
        return

    await set_language(query.from_user.id, lang)

    # First-time onboarding nudge — shown once after language select for new users
    user = await get_user(query.from_user.id)
    has_wallet = bool((user or {}).get("wallet_address"))

    _cta = {
        "ru": "\n\n👆 <i>Нажми Intel Feed — живые сигналы за 10 секунд</i>",
        "en": "\n\n👆 <i>Tap Intel Feed — live signals in 10 seconds</i>",
        "es": "\n\n👆 <i>Toca Intel Feed — señales en vivo en 10 segundos</i>",
        "pt": "\n\n👆 <i>Toque Intel Feed — sinais ao vivo em 10 segundos</i>",
        "tr": "\n\n👆 <i>Intel Feed'e dokun — 10 saniyede canlı sinyaller</i>",
        "id": "\n\n👆 <i>Tap Intel Feed — sinyal langsung dalam 10 detik</i>",
        "zh": "\n\n👆 <i>点击 Intel Feed — 10秒内获取实时信号</i>",
        "ar": "\n\n👆 <i>اضغط على Intel Feed — إشارات حية في 10 ثوانٍ</i>",
        "fr": "\n\n👆 <i>Appuie sur Intel Feed — signaux en direct en 10 secondes</i>",
        "de": "\n\n👆 <i>Intel Feed antippen — Live-Signale in 10 Sekunden</i>",
        "hi": "\n\n👆 <i>Intel Feed टैप करें — 10 सेकंड में लाइव सिग्नल</i>",
        "ja": "\n\n👆 <i>Intel Feedをタップ — 10秒でライブシグナル</i>",
    }
    nudge = _cta.get(lang, _cta["en"]) if not has_wallet else ""

    # Сразу показываем главное меню на новом языке
    await query.edit_message_text(
        WELCOME[lang] + nudge,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(MAIN_MENU[lang])
    )


async def cb_main_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Callback to return to main menu from any callback."""
    query = update.callback_query
    await query.answer()
    user = await get_user(query.from_user.id)
    lang = (user or {}).get("language")

    # Default to auto-detected language if not set
    if not lang:
        lang = _get_user_language(query.from_user.language_code or "en")

    await query.edit_message_text(
        WELCOME[lang],
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(MAIN_MENU[lang])
    )
