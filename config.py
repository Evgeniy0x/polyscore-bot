# PolyScore — Конфигурация
# Заполни свои ключи в .env или напрямую здесь для теста

import os
from dotenv import load_dotenv

# Загружаем .env файл — ищем рядом с этим файлом
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

# ─── Telegram ──────────────────────────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# ─── OpenRouter (как в Valli) ──────────────────────────────────────────────────
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
AI_MODEL_FAST   = "google/gemini-2.0-flash-001"    # Быстрые задачи
AI_MODEL_SMART  = "anthropic/claude-sonnet-4"       # Аналитика + прогнозы

# ─── Polymarket ────────────────────────────────────────────────────────────────
# Gamma API — публичный, ключ не нужен
GAMMA_API_URL = "https://gamma-api.polymarket.com"

# CLOB API — нужен для торговли (ключ из polymarket.com/settings?tab=builder)
CLOB_API_URL  = "https://clob.polymarket.com"
POLY_API_KEY    = os.getenv("POLY_API_KEY",    "")   # Builder API key
POLY_SECRET     = os.getenv("POLY_SECRET",     "")   # Builder API secret
POLY_PASSPHRASE = os.getenv("POLY_PASSPHRASE", "")   # Builder API passphrase
# Private key of the TRADING wallet (Polygon) — used to sign CLOB orders.
# NEVER commit this value. Set via environment variable only.
POLY_PRIVATE_KEY = os.getenv("POLY_PRIVATE_KEY", "")  # 0x... Polygon private key

# Builder Relayer — для создания gasless-кошельков пользователей
RELAYER_URL   = "https://relayer-v2.polymarket.com"
BUILDER_CODE  = os.getenv("BUILDER_CODE", "polyscore")  # твой builder code
RELAYER_API_KEY         = os.getenv("RELAYER_API_KEY", "")
RELAYER_API_KEY_ADDRESS = os.getenv("RELAYER_API_KEY_ADDRESS", "")

# Builder API Key — для атрибуции сделок и получения builder rewards
# Отдельный набор ключей от CLOB API (POLY_API_KEY).
# Генерируется на https://polymarket.com/settings?tab=builder
BUILDER_API_KEY    = os.getenv("BUILDER_API_KEY", "")
BUILDER_SECRET     = os.getenv("BUILDER_SECRET", "")
BUILDER_PASSPHRASE = os.getenv("BUILDER_PASSPHRASE", "")

# ─── Database ──────────────────────────────────────────────────────────────────
DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "polyscore.db"))

# ─── Категории рынков Polymarket ─────────────────────────────────────────────────
# Все теги, которые поддерживает Gamma API через tag_slug

# Спорт
SPORT_TAGS = [
    "sports", "baseball", "basketball", "hockey",
    "soccer", "football", "tennis", "mma", "formula-1",
]

# Все категории (включая не-спорт)
ALL_TAGS = SPORT_TAGS + [
    "crypto",        # Bitcoin, Ethereum, цены, DeFi
    "politics",      # Выборы, законы, геополитика
    "pop-culture",   # Кино, музыка, знаменитости
    "business",      # Компании, IPO, Earnings
    "science",       # Наука, климат, космос
    "world",         # Международные события
]

# ─── Эмодзи для категорий ────────────────────────────────────────────────────────
SPORT_EMOJI = {
    # Спорт
    "baseball":    "⚾",
    "basketball":  "🏀",
    "hockey":      "🏒",
    "soccer":      "⚽",
    "football":    "🏈",
    "tennis":      "🎾",
    "mma":         "🥊",
    "formula-1":   "🏎️",
    "sports":      "🏆",
    # Не-спорт
    "crypto":      "₿",
    "politics":    "🏛️",
    "pop-culture": "🎬",
    "business":    "💼",
    "science":     "🔬",
    "world":       "🌍",
    "all":         "📊",
}

# ─── Человекочитаемые названия категорий (RU / EN) ────────────────────────────────
CATEGORY_NAMES = {
    "ru": {
        "sports": "Все виды спорта", "baseball": "MLB Бейсбол",
        "basketball": "NBA Баскетбол", "hockey": "NHL Хоккей",
        "soccer": "Футбол", "football": "NFL", "tennis": "Теннис",
        "mma": "UFC / MMA", "formula-1": "Формула 1",
        "crypto": "Крипто", "politics": "Политика",
        "pop-culture": "Поп-культура", "business": "Бизнес",
        "science": "Наука", "world": "Мир",
    },
    "en": {
        "sports": "All Sports", "baseball": "MLB Baseball",
        "basketball": "NBA Basketball", "hockey": "NHL Hockey",
        "soccer": "Soccer", "football": "NFL Football", "tennis": "Tennis",
        "mma": "UFC / MMA", "formula-1": "Formula 1",
        "crypto": "Crypto", "politics": "Politics",
        "pop-culture": "Pop Culture", "business": "Business",
        "science": "Science", "world": "World",
    },
}

# ─── Настройки UI ──────────────────────────────────────────────────────────────
MAX_MARKETS_PER_PAGE = 5      # Рынков на одну страницу
MAX_PARLAY_LEGS      = 5      # Максимум ног в парлее
MIN_BET_AMOUNT       = 1.0    # Минимальная ставка (USDC)

# ─── Цвета для bet slip cards ──────────────────────────────────────────────────
CARD_BG_COLOR        = "#0D1117"   # Тёмный фон
CARD_ACCENT_GREEN    = "#00FF88"   # YES / победа
CARD_ACCENT_RED      = "#FF4466"   # NO / проигрыш
CARD_TEXT_COLOR      = "#FFFFFF"
CARD_MUTED_COLOR     = "#8B949E"
