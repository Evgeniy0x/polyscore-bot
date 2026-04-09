# PolyScore — База данных (SQLite async)
# Хранит: пользователей, кошельки, парлеи, историю ставок

import aiosqlite
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH
from services.crypto import encrypt_private_key, decrypt_private_key


# ══════════════════════════════════════════════════════════════════════
# Инициализация БД
# ══════════════════════════════════════════════════════════════════════

async def init_db():
    """Создать таблицы если не существуют."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id       INTEGER PRIMARY KEY,
                username      TEXT,
                language      TEXT DEFAULT 'ru',
                wallet_address TEXT,
                signer_address TEXT,
                private_key   TEXT DEFAULT '',
                created_at    TEXT DEFAULT (datetime('now')),
                last_seen     TEXT DEFAULT (datetime('now'))
            )
        """)
        # Добавить private_key если таблица уже существует (миграция)
        try:
            await db.execute("ALTER TABLE users ADD COLUMN private_key TEXT DEFAULT ''")
        except Exception:
            pass  # Колонка уже существует

        await db.execute("""
            CREATE TABLE IF NOT EXISTS bets (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER,
                market_id     TEXT,
                question      TEXT,
                outcome       TEXT,
                amount        REAL,
                price         REAL,
                potential_win REAL,
                order_id      TEXT,
                token_id      TEXT DEFAULT '',
                status        TEXT DEFAULT 'pending',
                created_at    TEXT DEFAULT (datetime('now'))
            )
        """)
        # Миграции: добавить колонки если таблица уже существует
        for col in ["token_id TEXT DEFAULT ''", "slug TEXT DEFAULT ''"]:
            try:
                await db.execute(f"ALTER TABLE bets ADD COLUMN {col}")
            except Exception:
                pass  # Колонка уже существует

        await db.execute("""
            CREATE TABLE IF NOT EXISTS parlays (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER,
                legs          TEXT,           -- JSON список ног
                total_odds    REAL,
                total_amount  REAL,
                potential_win REAL,
                status        TEXT DEFAULT 'active',
                created_at    TEXT DEFAULT (datetime('now'))
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                user_id       INTEGER,
                market_id     TEXT,
                question      TEXT,
                PRIMARY KEY (user_id, market_id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS copy_follows (
                user_id INTEGER,
                trader_address TEXT,
                trader_name TEXT DEFAULT '',
                copy_pct REAL DEFAULT 10.0,
                active INTEGER DEFAULT 1,
                last_trade_id TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (user_id, trader_address)
            )
        """)

        # Таблица прогресса Академии
        await db.execute("""
            CREATE TABLE IF NOT EXISTS academy_progress (
                user_id             INTEGER PRIMARY KEY,
                completed_lessons   TEXT DEFAULT '[]',  -- JSON список "module:lesson"
                total_xp            INTEGER DEFAULT 0,
                achievements        TEXT DEFAULT '[]',  -- JSON список id
                updated_at          TEXT DEFAULT (datetime('now'))
            )
        """)

        # Таблица алертов на цену
        await db.execute("""
            CREATE TABLE IF NOT EXISTS price_alerts (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                market_id   TEXT NOT NULL,
                question    TEXT NOT NULL,
                target_price REAL NOT NULL,
                direction   TEXT NOT NULL,  -- 'above' или 'below'
                triggered   INTEGER DEFAULT 0,
                created_at  TEXT DEFAULT (datetime('now'))
            )
        """)

        # Кэш реальных позиций с Polymarket (data-api)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS positions_cache (
                user_id      INTEGER NOT NULL,
                condition_id TEXT NOT NULL,
                data_json    TEXT NOT NULL,   -- JSON объект позиции
                synced_at    TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (user_id, condition_id)
            )
        """)

        await db.commit()
    print("[DB] Таблицы готовы.")


# ══════════════════════════════════════════════════════════════════════
# Пользователи
# ══════════════════════════════════════════════════════════════════════

async def get_user(user_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def create_user(user_id: int, username: str = "", language: str = "ru") -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT OR IGNORE INTO users (user_id, username, language)
               VALUES (?, ?, ?)""",
            (user_id, username, language)
        )
        await db.execute(
            "UPDATE users SET last_seen = datetime('now') WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()
    return await get_user(user_id)


async def set_wallet(user_id: int, wallet_address: str, signer_address: str = ""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE users
               SET wallet_address = ?, signer_address = ?
               WHERE user_id = ?""",
            (wallet_address, signer_address, user_id)
        )
        await db.commit()


async def set_language(user_id: int, language: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET language = ? WHERE user_id = ?",
            (language, user_id)
        )
        await db.commit()


async def update_user_wallet(user_id: int, wallet_address: str):
    """Update user's wallet address."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET wallet_address = ? WHERE user_id = ?",
            (wallet_address, user_id)
        )
        await db.commit()


async def save_generated_wallet(user_id: int, wallet_address: str, signer_address: str, private_key: str):
    """Сохранить авто-сгенерированный кошелёк (Safe + EOA приватный ключ).
    Приватный ключ шифруется AES-256 перед сохранением в БД.
    """
    encrypted_key = encrypt_private_key(private_key)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE users
               SET wallet_address = ?, signer_address = ?, private_key = ?
               WHERE user_id = ?""",
            (wallet_address, signer_address, encrypted_key, user_id)
        )
        await db.commit()


async def get_user_private_key(user_id: int) -> str:
    """Получить приватный ключ пользователя (для подписи транзакций).
    Автоматически дешифрует AES-256 ключ из БД.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT private_key FROM users WHERE user_id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
            if not row or not row[0]:
                return ""
            return decrypt_private_key(row[0])


# ══════════════════════════════════════════════════════════════════════
# Ставки
# ══════════════════════════════════════════════════════════════════════

async def save_bet(
    user_id:      int,
    market_id:    str,
    question:     str,
    outcome:      str,
    amount:       float,
    price:        float,
    order_id:     str = "",
    token_id:     str = "",
    slug:         str = "",
) -> int:
    potential_win = amount / price if price > 0 else 0
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO bets
               (user_id, market_id, question, outcome, amount, price, potential_win, order_id, token_id, slug)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, market_id, question, outcome, amount, price, potential_win, order_id, token_id, slug)
        )
        await db.commit()
        return cur.lastrowid


async def get_user_bets(user_id: int, limit: int = 20) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT * FROM bets WHERE user_id = ?
               ORDER BY created_at DESC LIMIT ?""",
            (user_id, limit)
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def get_user_stats(user_id: int) -> dict:
    """Статистика пользователя для профиля."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """SELECT
                COUNT(*) as total_bets,
                SUM(amount) as total_invested,
                SUM(potential_win) as total_potential
               FROM bets WHERE user_id = ?""",
            (user_id,)
        ) as cur:
            row = await cur.fetchone()
            return {
                "total_bets":       row[0] or 0,
                "total_invested":   row[1] or 0.0,
                "total_potential":  row[2] or 0.0,
            }


# ══════════════════════════════════════════════════════════════════════
# Парлеи
# ══════════════════════════════════════════════════════════════════════

async def save_parlay(
    user_id:       int,
    legs:          list[dict],
    total_odds:    float,
    total_amount:  float,
) -> int:
    potential_win = total_amount * total_odds
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO parlays
               (user_id, legs, total_odds, total_amount, potential_win)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, json.dumps(legs), total_odds, total_amount, potential_win)
        )
        await db.commit()
        return cur.lastrowid


async def get_user_parlays(user_id: int, limit: int = 10) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT * FROM parlays WHERE user_id = ?
               ORDER BY created_at DESC LIMIT ?""",
            (user_id, limit)
        ) as cur:
            rows = await cur.fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d["legs"] = json.loads(d["legs"])
                result.append(d)
            return result


# ══════════════════════════════════════════════════════════════════════
# Watchlist
# ══════════════════════════════════════════════════════════════════════

async def add_to_watchlist(user_id: int, market_id: str, question: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT OR REPLACE INTO watchlist (user_id, market_id, question)
               VALUES (?, ?, ?)""",
            (user_id, market_id, question)
        )
        await db.commit()


async def get_watchlist(user_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM watchlist WHERE user_id = ?",
            (user_id,)
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


# ══════════════════════════════════════════════════════════════════════
# Price Alerts
# ══════════════════════════════════════════════════════════════════════

async def add_price_alert(user_id: int, market_id: str, question: str,
                          target_price: float, direction: str) -> int:
    """Добавить алерт на цену. direction: 'above' | 'below'. Возвращает id алерта."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO price_alerts (user_id, market_id, question, target_price, direction)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, market_id, question, target_price, direction)
        )
        await db.commit()
        return cur.lastrowid


async def get_user_alerts(user_id: int) -> list[dict]:
    """Получить активные алерты пользователя."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM price_alerts WHERE user_id = ? AND triggered = 0 ORDER BY created_at DESC",
            (user_id,)
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def delete_alert(alert_id: int, user_id: int):
    """Удалить алерт пользователя."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM price_alerts WHERE id = ? AND user_id = ?",
            (alert_id, user_id)
        )
        await db.commit()


async def get_all_active_alerts() -> list[dict]:
    """Получить все активные алерты (для фонового воркера)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM price_alerts WHERE triggered = 0"
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def mark_alert_triggered(alert_id: int):
    """Пометить алерт как сработавший."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE price_alerts SET triggered = 1 WHERE id = ?",
            (alert_id,)
        )
        await db.commit()


# ══════════════════════════════════════════════════════════════════════
# Leaderboard
# ══════════════════════════════════════════════════════════════════════

async def get_leaderboard(limit: int = 10) -> list[dict]:
    """Get top players by total profit.

    Returns list of {user_id, username, total_profit, win_rate, bet_count}
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT
                u.user_id,
                u.username,
                COALESCE(SUM(b.potential_win - b.amount), 0) as total_profit,
                COALESCE(
                    ROUND(COUNT(CASE WHEN b.status = 'won' THEN 1 END) * 100.0 /
                    NULLIF(COUNT(*), 0), 1),
                    0
                ) as win_rate,
                COUNT(*) as bet_count
            FROM users u
            LEFT JOIN bets b ON u.user_id = b.user_id
            GROUP BY u.user_id, u.username
            HAVING COUNT(*) > 0
            ORDER BY total_profit DESC
            LIMIT ?
            """,
            (limit,)
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


# ══════════════════════════════════════════════════════════════════════
# Copy Trading — следим за трейдерами и копируем их сделки
# ══════════════════════════════════════════════════════════════════════

async def follow_trader(user_id: int, trader_address: str, copy_pct: float, trader_name: str = ""):
    """Подписаться на трейдера для копирования сделок."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT OR REPLACE INTO copy_follows
               (user_id, trader_address, trader_name, copy_pct, active)
               VALUES (?, ?, ?, ?, 1)""",
            (user_id, trader_address, trader_name, copy_pct)
        )
        await db.commit()


async def unfollow_trader(user_id: int, trader_address: str):
    """Отписаться от трейдера."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """DELETE FROM copy_follows
               WHERE user_id = ? AND trader_address = ?""",
            (user_id, trader_address)
        )
        await db.commit()


async def get_followed_traders(user_id: int) -> list[dict]:
    """Получить список следимых трейдеров для конкретного пользователя."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT user_id, trader_address, trader_name, copy_pct, active, last_trade_id, created_at
               FROM copy_follows
               WHERE user_id = ?
               ORDER BY created_at DESC""",
            (user_id,)
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def get_all_followed_traders() -> list[dict]:
    """Получить все пары (user_id, trader_address) для мониторинга."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT user_id, trader_address, trader_name, copy_pct, active, last_trade_id
               FROM copy_follows
               WHERE active = 1"""
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def toggle_copy_trading(user_id: int, active: bool):
    """Включить/выключить все копирование для пользователя."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE copy_follows
               SET active = ?
               WHERE user_id = ?""",
            (1 if active else 0, user_id)
        )
        await db.commit()


async def update_last_seen_trade(trader_address: str, trade_id: str):
    """Обновить последнюю видённую сделку трейдера (для всех подписчиков)."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE copy_follows
               SET last_trade_id = ?
               WHERE trader_address = ?""",
            (trade_id, trader_address)
        )
        await db.commit()


async def get_last_seen_trade(trader_address: str) -> str:
    """Получить ID последней видённой сделки трейдера."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """SELECT last_trade_id FROM copy_follows
               WHERE trader_address = ?
               LIMIT 1""",
            (trader_address,)
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else ""


# ══════════════════════════════════════════════════════════════════════
# Academy Progress
# ══════════════════════════════════════════════════════════════════════

async def get_academy_progress(user_id: int) -> dict:
    """Получить прогресс пользователя в Академии."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM academy_progress WHERE user_id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
            if not row:
                return {"completed_lessons": [], "total_xp": 0, "achievements": []}
            return {
                "completed_lessons": json.loads(row["completed_lessons"] or "[]"),
                "total_xp":          row["total_xp"] or 0,
                "achievements":      json.loads(row["achievements"] or "[]"),
            }


async def save_academy_progress(user_id: int, completed_lessons: list, total_xp: int,
                                 achievements: list = None):
    """Сохранить прогресс пользователя в Академии."""
    if achievements is None:
        existing = await get_academy_progress(user_id)
        achievements = existing.get("achievements", [])
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO academy_progress (user_id, completed_lessons, total_xp, achievements, updated_at)
               VALUES (?, ?, ?, ?, datetime('now'))
               ON CONFLICT(user_id) DO UPDATE SET
                   completed_lessons = excluded.completed_lessons,
                   total_xp          = excluded.total_xp,
                   achievements      = excluded.achievements,
                   updated_at        = excluded.updated_at""",
            (user_id,
             json.dumps(completed_lessons),
             total_xp,
             json.dumps(achievements))
        )
        await db.commit()


# ══════════════════════════════════════════════════════════════════════
# Positions Cache — реальные позиции с Polymarket
# ══════════════════════════════════════════════════════════════════════

async def upsert_positions(user_id: int, positions: list[dict]):
    """Сохранить/обновить список позиций пользователя (заменяет старые).
    Каждая позиция должна иметь ключ 'conditionId' или 'condition_id'.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        for pos in positions:
            condition_id = pos.get("conditionId") or pos.get("condition_id", "")
            if not condition_id:
                continue
            await db.execute(
                """INSERT INTO positions_cache (user_id, condition_id, data_json, synced_at)
                   VALUES (?, ?, ?, datetime('now'))
                   ON CONFLICT(user_id, condition_id) DO UPDATE SET
                       data_json = excluded.data_json,
                       synced_at = excluded.synced_at""",
                (user_id, condition_id, json.dumps(pos))
            )
        await db.commit()


async def get_cached_positions(user_id: int) -> list[dict]:
    """Получить закэшированные позиции пользователя."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT data_json, synced_at FROM positions_cache
               WHERE user_id = ?
               ORDER BY synced_at DESC""",
            (user_id,)
        ) as cur:
            rows = await cur.fetchall()
            result = []
            for r in rows:
                try:
                    pos = json.loads(r["data_json"])
                    pos["_synced_at"] = r["synced_at"]
                    result.append(pos)
                except Exception:
                    pass
            return result


async def clear_positions_cache(user_id: int):
    """Очистить кэш позиций пользователя (например, при смене кошелька)."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM positions_cache WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()


async def get_users_with_wallets() -> list[dict]:
    """Получить всех пользователей у кого есть кошелёк (для фонового синка позиций)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT user_id, wallet_address, language
               FROM users
               WHERE wallet_address IS NOT NULL AND wallet_address != ''"""
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]
