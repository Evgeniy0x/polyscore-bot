# PolyScore — Перевод названий рынков
#
# Переводит названия рынков с Polymarket (английский) на язык пользователя.
# Результаты кешируются в SQLite чтобы не тратить время и ресурсы на повторные запросы.
# Если перевод недоступен — возвращает оригинальный английский текст.

import aiosqlite
import asyncio
import hashlib
import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH

logger = logging.getLogger("PolyScore.translator")

# Языки которые НЕ нужно переводить (оригинал уже на них)
SKIP_LANGS = {"en"}

# Маппинг языковых кодов PolyScore → deep-translator
LANG_MAP = {
    "ru": "russian",
    "es": "spanish",
    "pt": "portuguese",
    "tr": "turkish",
    "id": "indonesian",
    "zh": "chinese (simplified)",
    "ar": "arabic",
    "fr": "french",
    "de": "german",
    "hi": "hindi",
    "ja": "japanese",
}


async def _ensure_cache_table():
    """Создать таблицу кеша переводов если не существует."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS translation_cache (
                hash     TEXT PRIMARY KEY,
                lang     TEXT NOT NULL,
                original TEXT NOT NULL,
                translated TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        await db.commit()


def _cache_key(text: str, lang: str) -> str:
    """Уникальный ключ для кеша."""
    return hashlib.md5(f"{lang}:{text}".encode()).hexdigest()


async def _get_cached(text: str, lang: str) -> str | None:
    """Получить перевод из кеша."""
    key = _cache_key(text, lang)
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT translated FROM translation_cache WHERE hash = ?", (key,)
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else None


async def _save_cache(text: str, lang: str, translated: str):
    """Сохранить перевод в кеш."""
    key = _cache_key(text, lang)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO translation_cache (hash, lang, original, translated) VALUES (?, ?, ?, ?)",
            (key, lang, text, translated)
        )
        await db.commit()


def _translate_sync(text: str, lang: str) -> str:
    """Синхронный перевод через deep-translator (вызывается в executor)."""
    try:
        from deep_translator import GoogleTranslator
        target = LANG_MAP.get(lang, "english")
        result = GoogleTranslator(source="english", target=target).translate(text)
        return result if result else text
    except Exception as e:
        logger.warning(f"Translation failed for lang={lang}: {e}")
        return text


async def translate_market_name(text: str, lang: str) -> str:
    """
    Перевести название рынка на язык пользователя.
    Использует кеш — повторные запросы мгновенные.

    Args:
        text: Оригинальное название рынка (английский)
        lang: Код языка пользователя (ru, es, zh, ...)

    Returns:
        Переведённое название, или оригинал если перевод недоступен
    """
    if not text or lang in SKIP_LANGS:
        return text

    # Проверяем кеш
    cached = await _get_cached(text, lang)
    if cached:
        return cached

    # Переводим в отдельном потоке (sync библиотека)
    try:
        loop = asyncio.get_event_loop()
        translated = await loop.run_in_executor(None, _translate_sync, text, lang)
        if translated and translated != text:
            await _save_cache(text, lang, translated)
        return translated
    except Exception as e:
        logger.warning(f"Translation error: {e}")
        return text


async def translate_many(texts: list[str], lang: str) -> list[str]:
    """
    Перевести список названий рынков пакетом.
    Сначала проверяет кеш, потом переводит только незакешированные.
    """
    if lang in SKIP_LANGS:
        return texts

    results = []
    to_translate = []
    indices = []

    # Разделяем: что в кеше, что нет
    for i, text in enumerate(texts):
        cached = await _get_cached(text, lang)
        if cached:
            results.append(cached)
        else:
            results.append(text)  # временно оригинал
            to_translate.append((i, text))
            indices.append(i)

    # Переводим незакешированные
    for i, text in to_translate:
        translated = await translate_market_name(text, lang)
        results[i] = translated

    return results


# Инициализация кеша при импорте
async def init_translator():
    """Вызвать при старте бота."""
    await _ensure_cache_table()
