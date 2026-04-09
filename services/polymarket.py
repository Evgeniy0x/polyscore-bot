# PolyScore — Polymarket API клиент
# Gamma API (публичные данные) + CLOB API (торговля)

import aiohttp
import asyncio
import json
import time
import hmac
import hashlib
import base64
from typing import Optional
from datetime import datetime, timezone
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    GAMMA_API_URL, CLOB_API_URL, RELAYER_URL,
    POLY_API_KEY, POLY_SECRET, POLY_PASSPHRASE, BUILDER_CODE,
    BUILDER_API_KEY, BUILDER_SECRET, BUILDER_PASSPHRASE,
    RELAYER_API_KEY, RELAYER_API_KEY_ADDRESS,
    SPORT_TAGS
)


# ══════════════════════════════════════════════════════════════════════
# GAMMA API — публичные данные о рынках (не требует авторизации)
# ══════════════════════════════════════════════════════════════════════

class GammaClient:
    """Клиент для Polymarket Gamma API — рыночные данные."""

    def __init__(self):
        self.base = GAMMA_API_URL
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={"User-Agent": "PolyScore/1.0"}
            )
        return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    # Маппинг наших тегов → slug для /events эндпоинта Gamma API
    TAG_TO_SLUG = {
        # Спорт
        "sports":      "sports",
        "baseball":    "mlb",
        "basketball":  "nba",
        "hockey":      "nhl",
        "soccer":      "soccer",
        "football":    "nfl",
        "tennis":      "tennis",
        "mma":         "ufc",
        "formula-1":   "formula-1",
        # Не-спорт
        "crypto":      "crypto",
        "politics":    "politics",
        "pop-culture": "pop-culture",
        "business":    "business",
        "science":     "science",
        "world":       "world",
    }

    @staticmethod
    def _is_market_tradable(market: dict) -> bool:
        """
        Проверяет что рынок реально открыт для торговли:
        1. endDate > now (не истёк по времени)
        2. Имеет хотя бы один token_id (CLOB может его исполнить)
        Рынки без этих условий вызывают ошибку 'Не удалось получить ID токена'.
        """
        now = datetime.now(timezone.utc)

        # Проверка 1: дата закрытия ещё не наступила
        end_date_str = market.get("endDate") or market.get("end_date_utc") or ""
        if end_date_str:
            try:
                # Gamma API возвращает ISO-формат: 2025-12-31T23:59:00Z
                end_dt = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
                if end_dt <= now:
                    return False
            except (ValueError, TypeError):
                pass  # если дата не парсится — не исключаем рынок

        # Проверка 2: есть clobTokenIds — значит рынок торгуется на CLOB
        # /events endpoint возвращает clobTokenIds как JSON-строку ["tokenYES","tokenNO"]
        # tokens[] всегда пустой в /events ответах — не используем
        clob_ids_raw = market.get("clobTokenIds")
        if clob_ids_raw is not None:
            try:
                import json as _j
                ids = _j.loads(clob_ids_raw) if isinstance(clob_ids_raw, str) else clob_ids_raw
                if not ids or not any(ids):
                    return False
            except Exception:
                return False

        return True

    async def get_sports_markets(
        self,
        limit: int = 20,
        offset: int = 0,
        tag: str = "sports"
    ) -> list[dict]:
        """
        Получить список рынков через /events эндпоинт.
        Фильтрует по endDate > now и наличию token_id.
        tag: 'sports', 'baseball', 'basketball', 'hockey', 'soccer', etc.
        """
        session = await self._get_session()
        slug = self.TAG_TO_SLUG.get(tag, tag)
        # Запрашиваем с запасом чтобы после фильтрации осталось достаточно рынков
        fetch_limit = limit * 3
        params = {
            "limit": fetch_limit,
            "offset": offset,
            "active": "true",
            "closed": "false",
            "tag_slug": slug,
        }
        try:
            async with session.get(f"{self.base}/events", params=params) as resp:
                if resp.status == 200:
                    events = await resp.json()
                    if not isinstance(events, list):
                        events = events.get("data", [])
                    markets = []
                    for event in events:
                        event_markets = event.get("markets", [])
                        if event_markets:
                            for m in event_markets:
                                m["_event_title"] = event.get("title", "")
                                m["_event_slug"] = event.get("slug", "")
                                # Фильтр: только рынки с будущей датой и token_id
                                if self._is_market_tradable(m):
                                    markets.append(m)
                        else:
                            if self._is_market_tradable(event):
                                markets.append(event)
                    return markets[:limit]
                return []
        except Exception as e:
            print(f"[Gamma] Ошибка get_sports_markets: {e}")
            return []

    async def get_market(self, market_id: str) -> Optional[dict]:
        """Получить детальную информацию о рынке по ID или slug."""
        session = await self._get_session()
        try:
            # Пробуем по condition_id
            async with session.get(f"{self.base}/markets/{market_id}") as resp:
                if resp.status == 200:
                    return await resp.json()
            # Пробуем поиск по slug
            async with session.get(
                f"{self.base}/markets",
                params={"slug": market_id, "limit": 1}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    markets = data if isinstance(data, list) else data.get("data", [])
                    return markets[0] if markets else None
        except Exception as e:
            print(f"[Gamma] Ошибка get_market: {e}")
        return None

    async def search_markets(self, query: str, limit: int = 10) -> list[dict]:
        """Поиск рынков по тексту."""
        session = await self._get_session()
        try:
            async with session.get(
                f"{self.base}/markets",
                params={"q": query, "limit": limit, "active": "true"}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data if isinstance(data, list) else data.get("data", [])
        except Exception as e:
            print(f"[Gamma] Ошибка search: {e}")
        return []

    async def get_market_prices(self, slug_or_id: str) -> Optional[dict]:
        """
        Получить цены и token_ids для рынка по slug или numeric id.
        NOTE: /markets/{conditionId} возвращает 422 — не использовать conditionId здесь.
        Правильный путь: /markets?slug=... или /markets/{numeric_id}.
        """
        session = await self._get_session()
        try:
            # Try slug lookup first (slug is always available from /events market)
            async with session.get(
                f"{self.base}/markets",
                params={"slug": slug_or_id, "limit": 1}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    markets = data if isinstance(data, list) else data.get("data", [])
                    if markets:
                        market = markets[0]
                        # Try tokens[] first (present on /markets endpoint)
                        tokens = market.get("tokens", [])
                        if tokens:
                            result = {}
                            for token in tokens:
                                outcome = token.get("outcome", "").upper()
                                result[outcome] = {
                                    "price": float(token.get("price", 0)),
                                    "token_id": token.get("token_id", ""),
                                }
                            if result:
                                return result
                        # Fallback: parse clobTokenIds
                        clob_ids_raw = market.get("clobTokenIds")
                        if clob_ids_raw:
                            import json as _j
                            ids = _j.loads(clob_ids_raw) if isinstance(clob_ids_raw, str) else clob_ids_raw
                            prices_raw = market.get("outcomePrices")
                            prices_list = []
                            if prices_raw:
                                try:
                                    prices_list = _j.loads(prices_raw) if isinstance(prices_raw, str) else prices_raw
                                except Exception:
                                    pass
                            if len(ids) >= 2:
                                return {
                                    "YES": {"token_id": ids[0], "price": float(prices_list[0]) if len(prices_list) > 0 else 0.5},
                                    "NO":  {"token_id": ids[1], "price": float(prices_list[1]) if len(prices_list) > 1 else 0.5},
                                }
        except Exception as e:
            print(f"[Gamma] Ошибка get_prices: {e}")
        return None

    async def get_prices_by_condition(self, condition_id: str) -> Optional[dict]:
        """
        Получить текущие цены и token_ids по condition_id рынка.
        Пробует несколько API в порядке надёжности:
          1. Gamma /markets?condition_id=...
          2. Gamma /events?slug=... (events содержат outcomePrices)
          3. CLOB /prices?token_id=... (если token_id известен)
        Возвращает: {"YES": {"price": 0.54, "token_id": "..."}, "NO": ...}
        """
        import json as _j
        session = await self._get_session()

        # ── Strategy 1: Gamma /markets?condition_id= ─────────────────────
        try:
            async with session.get(
                f"{self.base}/markets",
                params={"condition_id": condition_id, "limit": 1}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    markets = data if isinstance(data, list) else data.get("data", [])
                    if markets:
                        result = self._parse_market_prices(markets[0])
                        if result:
                            print(f"[Gamma] Prices via condition_id OK: {condition_id[:16]}...")
                            return result
                    else:
                        print(f"[Gamma] condition_id returned empty: {condition_id[:16]}...")
        except Exception as e:
            print(f"[Gamma] Strategy 1 (condition_id) error: {e}")

        # ── Strategy 2: CLOB public /book endpoint ───────────────────────
        # CLOB не нуждается в condition_id — но нужен token_id.
        # Пропускаем этот шаг (нет token_id на этом уровне).

        # ── Strategy 3: Gamma /markets (по прямому ID) ───────────────────
        try:
            async with session.get(
                f"{self.base}/markets/{condition_id}"
            ) as resp:
                if resp.status == 200:
                    market = await resp.json()
                    if isinstance(market, dict):
                        result = self._parse_market_prices(market)
                        if result:
                            print(f"[Gamma] Prices via direct ID OK: {condition_id[:16]}...")
                            return result
        except Exception as e:
            print(f"[Gamma] Strategy 3 (direct ID) error: {e}")

        # ── Strategy 4: CLOB public price endpoint ───────────────────────
        try:
            clob_url = "https://clob.polymarket.com/prices"
            async with session.get(
                clob_url,
                params={"market": condition_id}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # CLOB /prices returns: {"YES": "0.54", "NO": "0.46"} or similar
                    if isinstance(data, dict) and ("YES" in data or "yes" in data):
                        yes_p = float(data.get("YES") or data.get("yes") or 0)
                        no_p = float(data.get("NO") or data.get("no") or 0)
                        if yes_p > 0 or no_p > 0:
                            print(f"[CLOB] Prices via /prices OK: YES={yes_p} NO={no_p}")
                            return {
                                "YES": {"price": yes_p, "token_id": ""},
                                "NO":  {"price": no_p, "token_id": ""},
                            }
        except Exception as e:
            print(f"[CLOB] Strategy 4 (/prices) error: {e}")

        print(f"[Gamma] ALL strategies failed for {condition_id[:20]}...")
        return None

    @staticmethod
    def _parse_market_prices(market: dict) -> Optional[dict]:
        """Извлечь цены и token_ids из объекта рынка Gamma API."""
        import json as _j
        # tokens[] (preferred)
        tokens = market.get("tokens", [])
        if tokens:
            result = {}
            for token in tokens:
                outcome = token.get("outcome", "").upper()
                result[outcome] = {
                    "price": float(token.get("price", 0)),
                    "token_id": token.get("token_id", ""),
                }
            if result:
                return result
        # Fallback: clobTokenIds + outcomePrices
        clob_ids_raw = market.get("clobTokenIds")
        if clob_ids_raw:
            ids = _j.loads(clob_ids_raw) if isinstance(clob_ids_raw, str) else clob_ids_raw
            prices_raw = market.get("outcomePrices")
            prices_list = []
            if prices_raw:
                try:
                    prices_list = _j.loads(prices_raw) if isinstance(prices_raw, str) else prices_raw
                except Exception:
                    pass
            if len(ids) >= 2:
                return {
                    "YES": {"token_id": ids[0], "price": float(prices_list[0]) if len(prices_list) > 0 else 0.5},
                    "NO":  {"token_id": ids[1], "price": float(prices_list[1]) if len(prices_list) > 1 else 0.5},
                }
        return None

    async def get_trending_markets(self, limit: int = 10, tag: str = None) -> list[dict]:
        """
        Горячие рынки по объёму за 24ч. tag=None → все категории.
        Использует тот же фильтр что и get_sports_markets:
        только рынки с endDate > now и наличием token_id.
        """
        session = await self._get_session()
        try:
            # Запрашиваем с запасом чтобы после фильтрации осталось достаточно рынков
            fetch_limit = limit * 3
            params = {
                "limit": fetch_limit,
                "active": "true",
                "closed": "false",
                "_order": "volume24hr",
            }
            if tag:
                params["tag_slug"] = self.TAG_TO_SLUG.get(tag, tag)

            async with session.get(
                f"{self.base}/events",
                params=params,
            ) as resp:
                if resp.status == 200:
                    events = await resp.json()
                    if not isinstance(events, list):
                        events = events.get("data", [])
                    markets = []
                    for event in events:
                        event_markets = event.get("markets", [])
                        if event_markets:
                            m = event_markets[0]
                            m["_event_title"] = event.get("title", "")
                            # Фильтр: только рынки с будущей датой и token_id
                            if self._is_market_tradable(m):
                                markets.append(m)
                        else:
                            if self._is_market_tradable(event):
                                markets.append(event)
                    return markets[:limit]
        except Exception as e:
            print(f"[Gamma] Ошибка trending: {e}")
        return []

    @staticmethod
    def extract_prices(market: dict) -> tuple[float, float]:
        """Извлечь цены YES/NO из любого формата рынка."""
        yes_price = no_price = 0.0

        # Формат 1: tokens (старый /markets эндпоинт)
        tokens = market.get("tokens", [])
        if tokens:
            for t in tokens:
                outcome = t.get("outcome", "").upper()
                price = float(t.get("price", 0) or 0)
                if outcome == "YES":
                    yes_price = price
                elif outcome == "NO":
                    no_price = price
            return yes_price, no_price

        # Формат 2: outcomePrices (новый /events эндпоинт)
        outcome_prices = market.get("outcomePrices")
        if outcome_prices:
            try:
                import json as _json
                prices = _json.loads(outcome_prices) if isinstance(outcome_prices, str) else outcome_prices
                if len(prices) >= 2:
                    yes_price = float(prices[0])
                    no_price = float(prices[1])
            except Exception:
                pass

        return yes_price, no_price

    @staticmethod
    def format_market(market: dict) -> str:
        """
        Форматировать рынок для Telegram-сообщения.
        Возвращает HTML-строку.
        """
        question   = market.get("question", market.get("title", "—"))
        volume24   = float(market.get("volume24hr", 0) or 0)
        end_date   = market.get("endDate", "")[:10] if market.get("endDate") else "—"
        market_id  = market.get("conditionId", market.get("id", ""))
        event_title = market.get("_event_title", "")

        yes_price, no_price = GammaClient.extract_prices(market)

        # Иконка вероятности
        if yes_price >= 0.70:
            mood = "🟢"
        elif yes_price >= 0.40:
            mood = "🟡"
        else:
            mood = "🔴"

        lines = [f"{mood} <b>{question}</b>"]
        if event_title and event_title != question:
            lines.append(f"  📁 {event_title}")
        lines += [
            f"",
            f"  YES: <b>{yes_price:.0%}</b>  |  NO: <b>{no_price:.0%}</b>",
            f"  💰 Объём 24ч: <b>${volume24:,.0f}</b>",
            f"  📅 До: {end_date}",
            f"  🔑 ID: <code>{market_id[:12]}...</code>",
        ]
        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════
# CLOB API — торговля (требует API-ключ Polymarket)
# ══════════════════════════════════════════════════════════════════════

class ClobClient:
    """
    Клиент для Polymarket CLOB API.
    Размещение ордеров, получение позиций, баланса.

    Документация: https://docs.polymarket.com/developers/clob-api/overview
    """

    def __init__(self):
        self.base    = CLOB_API_URL
        self.api_key = POLY_API_KEY
        self.secret  = POLY_SECRET
        self.passphrase = POLY_PASSPHRASE
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    def _make_auth_headers(self, method: str, path: str, body: str = "") -> dict:
        """
        Генерирует CLOB API auth headers.
        POLY-ADDRESS, POLY-SIGNATURE, POLY-TIMESTAMP, POLY-NONCE
        """
        if not self.api_key:
            return {}

        timestamp = str(int(time.time()))
        nonce     = "0"

        # Строка для подписи: timestamp + method + path + body
        message   = timestamp + method.upper() + path + body

        # HMAC-SHA256
        signature = hmac.new(
            self.secret.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()
        sig_b64   = base64.b64encode(signature).decode()

        headers = {
            "POLY-API-KEY":   self.api_key,
            "POLY-SIGNATURE": sig_b64,
            "POLY-TIMESTAMP": timestamp,
            "POLY-NONCE":     nonce,
            "Content-Type":   "application/json",
        }

        # Добавляем Builder headers для атрибуции сделок
        builder_headers = self._make_builder_headers(method, path, body)
        if builder_headers:
            headers.update(builder_headers)

        return headers

    def _make_builder_headers(self, method: str, path: str, body: str = "") -> dict:
        """
        Генерирует Builder API headers для атрибуции сделок.
        Без этих заголовков Polymarket не видит наши сделки как builder trades
        и мы не получаем builder rewards.

        Использует HMAC-SHA256 подпись аналогично CLOB auth headers.
        """
        if not all([BUILDER_API_KEY, BUILDER_SECRET, BUILDER_PASSPHRASE]):
            return {}

        timestamp = str(int(time.time()))

        # Строка для подписи: timestamp + method + path + body
        message = timestamp + method.upper() + path + (body or "")

        # HMAC-SHA256 подпись builder secret
        signature = hmac.new(
            base64.urlsafe_b64decode(BUILDER_SECRET),
            message.encode(),
            hashlib.sha256
        ).digest()
        sig_b64 = base64.urlsafe_b64encode(signature).decode()

        return {
            "POLY_BUILDER_API_KEY":    BUILDER_API_KEY,
            "POLY_BUILDER_TIMESTAMP":  timestamp,
            "POLY_BUILDER_PASSPHRASE": BUILDER_PASSPHRASE,
            "POLY_BUILDER_SIGNATURE":  sig_b64,
        }

    async def get_orderbook(self, token_id: str) -> Optional[dict]:
        """Получить orderbook для токена (YES или NO)."""
        session = await self._get_session()
        try:
            async with session.get(
                f"{self.base}/book",
                params={"token_id": token_id}
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception as e:
            print(f"[CLOB] Ошибка orderbook: {e}")
        return None

    async def get_midpoint_price(self, token_id: str) -> Optional[float]:
        """Получить mid-price для токена."""
        session = await self._get_session()
        try:
            async with session.get(
                f"{self.base}/midpoint",
                params={"token_id": token_id}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return float(data.get("mid", 0))
        except Exception as e:
            print(f"[CLOB] Ошибка midpoint: {e}")
        return None

    async def place_market_order(
        self,
        token_id:  str,
        side:      str,        # "BUY" или "SELL"
        amount:    float,      # в USDC
        funder:    str = "",   # адрес кошелька
    ) -> Optional[dict]:
        """
        Разместить маркет-ордер.

        Важно: ордер должен быть подписан приватным ключом кошелька.
        Для полноценной торговли нужен py-clob-client.
        Здесь — скелет с правильной структурой.
        """
        if not self.api_key:
            return {"error": "API key not configured. See /setup"}

        # Структура ордера для CLOB API
        order_body = {
            "tokenID":    token_id,
            "side":       side,
            "size":       str(amount),
            "orderType":  "FOK",          # Fill or Kill — маркет
            "builderCode": BUILDER_CODE,  # Наш builder code — главное!
            "funder":     funder,
        }

        body_str = json.dumps(order_body, separators=(",", ":"))
        headers  = self._make_auth_headers("POST", "/order", body_str)

        session = await self._get_session()
        try:
            async with session.post(
                f"{self.base}/order",
                data=body_str,
                headers=headers
            ) as resp:
                data = await resp.json()
                return data
        except Exception as e:
            print(f"[CLOB] Ошибка place_order: {e}")
            return {"error": str(e)}

    async def get_positions(self, address: str) -> list[dict]:
        """Получить позиции кошелька."""
        if not address:
            return []
        session = await self._get_session()
        path    = f"/positions"
        headers = self._make_auth_headers("GET", path)
        try:
            async with session.get(
                f"{self.base}{path}",
                params={"user": address},
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data if isinstance(data, list) else data.get("data", [])
        except Exception as e:
            print(f"[CLOB] Ошибка positions: {e}")
        return []

    async def get_balance(self, address: str) -> float:
        """Получить USDC баланс кошелька на Polygon.

        Проверяет оба контракта USDC (native + bridged) через надёжный RPC.
        Возвращает сумму — пользователь мог иметь оба вида USDC.
        """
        if not address:
            return 0.0
        session = await self._get_session()

        # Native USDC (Circle, новый) + USDC.e (bridged, старый)
        usdc_contracts = [
            "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",  # native USDC
            "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",  # USDC.e bridged
        ]
        # RPC с fallback — 1rpc.io подтверждён рабочим
        rpcs = [
            "https://1rpc.io/matic",
            "https://rpc.ankr.com/polygon",
        ]

        addr_padded = address[2:].lower()
        call_data = f"0x70a08231000000000000000000000000{addr_padded}"
        total = 0.0

        # Используем отдельную сессию с таймаутом — не зависим от основной
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as rpc_session:
            for contract in usdc_contracts:
                rpc_payload = {
                    "jsonrpc": "2.0",
                    "method":  "eth_call",
                    "params": [{"to": contract, "data": call_data}, "latest"],
                    "id": 1,
                }
                for rpc in rpcs:
                    try:
                        async with rpc_session.post(
                            rpc, json=rpc_payload,
                            headers={"Content-Type": "application/json"},
                        ) as resp:
                            if resp.status == 200:
                                result = await resp.json()
                                hex_val = result.get("result", "0x0") or "0x0"
                                if hex_val not in ("0x", "0x0"):
                                    raw = int(hex_val, 16)
                                    total += raw / 1_000_000  # USDC: 6 decimals
                                break  # успешный ответ — следующий контракт
                    except Exception as e:
                        print(f"[Balance] RPC {rpc} error: {e}")
                        continue  # пробуем следующий RPC

        print(f"[Balance] {address[:10]}... = ${total:.6f}")
        return total


# ══════════════════════════════════════════════════════════════════════
# Builder Relayer — создание gasless-кошельков для пользователей
# ══════════════════════════════════════════════════════════════════════

class RelayerClient:
    """
    Builder Relayer v2 — создаёт Safe-кошельки для пользователей.
    Пользователи не платят газ. Polymarket оплачивает за нас.
    """

    def __init__(self):
        self.base = RELAYER_URL
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if not self.session or self.session.closed:
            headers = {"Content-Type": "application/json"}
            if RELAYER_API_KEY:
                headers["RELAYER_API_KEY"] = RELAYER_API_KEY
                headers["RELAYER_API_KEY_ADDRESS"] = RELAYER_API_KEY_ADDRESS
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def create_wallet(self, signer_address: str) -> Optional[str]:
        """
        Создать Safe-кошелёк для пользователя.
        signer_address — EOA адрес пользователя (из телеграм-кошелька).
        Возвращает адрес Safe-кошелька.
        """
        session = await self._get_session()
        try:
            async with session.post(
                f"{self.base}/deploy-wallet",
                json={
                    "signer":      signer_address,
                    "builderCode": BUILDER_CODE,
                }
            ) as resp:
                if resp.status in (200, 201):
                    data = await resp.json()
                    return data.get("address") or data.get("safe")
                print(f"[Relayer] Deploy wallet failed: {resp.status} {await resp.text()}")
        except Exception as e:
            print(f"[Relayer] Ошибка create_wallet: {e}")
        return None

    async def approve_usdc(self, wallet_address: str) -> bool:
        """Выдать USDC approve для CTF контракта (gasless)."""
        session = await self._get_session()
        try:
            async with session.post(
                f"{self.base}/approve",
                json={
                    "address":     wallet_address,
                    "builderCode": BUILDER_CODE,
                }
            ) as resp:
                return resp.status in (200, 201)
        except Exception as e:
            print(f"[Relayer] Ошибка approve: {e}")
        return False


# ══════════════════════════════════════════════════════════════════════
# Вспомогательные функции
# ══════════════════════════════════════════════════════════════════════

def price_to_american_odds(price: float) -> str:
    """
    Конвертировать десятичную цену (0.0–1.0) в американские odds.
    Знакомый формат для спортивных бетторов.
    Примеры: 0.5 → +100, 0.67 → -200, 0.33 → +200
    """
    if price <= 0 or price >= 1:
        return "N/A"
    if price >= 0.5:
        odds = -round((price / (1 - price)) * 100)
    else:
        odds = round(((1 - price) / price) * 100)
    return f"+{odds}" if odds > 0 else str(odds)


def price_to_implied_prob(price: float) -> str:
    """Цена → строка вероятности для UI."""
    return f"{price:.0%}"


def format_volume(v: float) -> str:
    """Форматировать объём: 1500000 → $1.5M"""
    if v >= 1_000_000:
        return f"${v/1_000_000:.1f}M"
    elif v >= 1_000:
        return f"${v/1_000:.0f}K"
    return f"${v:.0f}"


# Синглтоны для переиспользования в handlers
gamma   = GammaClient()
clob    = ClobClient()
relayer = RelayerClient()
