# PolyScore — Signal Pipeline
# Генерация, фильтрация и доставка торговых сигналов
#
# Архитектура:
#   SignalCard — структура данных сигнала
#   SignalPipeline — генерация из нескольких источников
#   Источники: ai_model | whale_activity | mispricing | algo
#
# Интеграция:
#   handlers/intel.py читает сигналы через get_feed()
#   alerts_worker в bot.py вызывает push_signals() для уведомлений

import asyncio
import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional
import sys
import os

import aiohttp

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OPENROUTER_API_KEY, AI_MODEL_FAST, AI_MODEL_SMART


# ══════════════════════════════════════════════════════════════════════
# SIGNAL CARD — Единая структура сигнала
# ══════════════════════════════════════════════════════════════════════

@dataclass
class SignalCard:
    """
    Универсальная карточка торгового сигнала.
    Используется в Intel Mode, AI брифинге, copy trading и algo.
    """
    # Идентификация
    signal_id: str              # uuid-like или "{source}_{market_id}"
    market_id: str              # Polymarket conditionId или slug
    question: str               # Вопрос рынка

    # Направление и цена
    direction: str              # "YES" | "NO"
    current_price: float        # Текущая цена [0..1]
    fair_value: float           # Оценка истинной вероятности [0..1]

    # Метрики
    edge_pct: float             # Ожидаемое преимущество %
    confidence: float           # Уверенность [0..1]

    # Источник
    source: str                 # "ai_model" | "whale_activity" | "mispricing" | "algo"
    source_label: str           # "🤖 AI Model" | "🐋 Whale" | "📊 Arb" | "⚡ Algo"

    # Объяснение (одна строка каждое)
    reason: str                 # "Options market at 75%, PM at 67%"
    risk: str                   # "Low liquidity, spread ~3%"

    # Тайминг
    generated_at: float = field(default_factory=time.time)
    expires_in: int = 3600      # TTL в секундах (default 1 час)

    # Закрытие рынка
    market_closes: str = ""     # ISO date или ""

    # Исполнение
    suggested_amount: float = 10.0  # Рекомендованная сумма USDC
    priority: str = "MEDIUM"    # "HIGH" | "MEDIUM" | "LOW"

    # Служебные
    volume_24h: float = 0.0
    token_id: str = ""          # для CLOB исполнения

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.generated_at) > self.expires_in

    @property
    def price_display(self) -> str:
        return f"{self.current_price:.0%}"

    @property
    def edge_display(self) -> str:
        sign = "+" if self.edge_pct >= 0 else ""
        return f"{sign}{self.edge_pct:.1f}%"

    @property
    def priority_emoji(self) -> str:
        return {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "⚪"}.get(self.priority, "⚪")

    def to_telegram_text(self, lang: str = "ru") -> str:
        """Форматировать сигнал для отправки в Telegram."""
        closing = f"📅 {self.market_closes}" if self.market_closes else ""

        if lang == "ru":
            lines = [
                f"{self.priority_emoji} <b>{'ВЫСОКИЙ' if self.priority == 'HIGH' else 'СРЕДНИЙ' if self.priority == 'MEDIUM' else 'НИЗКИЙ'} СИГНАЛ</b>",
                "",
                f"📊 {self.question}",
                "",
                f"Направление: <b>{self.direction}</b>  {self.price_display}",
                f"Edge: <b>{self.edge_display}</b>  ·  Уверенность: {self.confidence:.0%}",
                f"Источник: {self.source_label}",
            ]
            if closing:
                lines.append(closing)
            lines += [
                "",
                f"💡 {self.reason}",
                f"⚠️ {self.risk}",
                "",
                f"💵 Рекомендовано: ${self.suggested_amount:.0f} USDC",
            ]
        else:
            lines = [
                f"{self.priority_emoji} <b>{'HIGH' if self.priority == 'HIGH' else 'MEDIUM' if self.priority == 'MEDIUM' else 'LOW'} SIGNAL</b>",
                "",
                f"📊 {self.question}",
                "",
                f"Direction: <b>{self.direction}</b>  {self.price_display}",
                f"Edge: <b>{self.edge_display}</b>  ·  Confidence: {self.confidence:.0%}",
                f"Source: {self.source_label}",
            ]
            if closing:
                lines.append(closing)
            lines += [
                "",
                f"💡 {self.reason}",
                f"⚠️  {self.risk}",
                "",
                f"💵 Suggested: ${self.suggested_amount:.0f} USDC",
            ]

        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════
# SIGNAL PIPELINE — Генератор сигналов
# ══════════════════════════════════════════════════════════════════════

class SignalPipeline:
    """
    Агрегирует сигналы из нескольких источников.
    Применяет приоритизацию и фильтрацию.
    """

    # Кеш последних сигналов (shared in-memory)
    _cache: list[SignalCard] = []
    _cache_time: float = 0
    _cache_ttl: int = 600  # 10 минут

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={"User-Agent": "PolyScore/2.0"}
            )
        return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    # ── Источник 1: AI Model (из ai_service) ─────────────────────────

    async def generate_ai_signals(
        self, markets: list[dict], max_signals: int = 5
    ) -> list[SignalCard]:
        """
        Генерирует сигналы через AI анализ рынков.
        Возвращает структурированные SignalCard, не просто текст.
        """
        if not OPENROUTER_API_KEY or not markets:
            return []

        signals = []
        # Анализируем топ рынки
        for market in markets[:max_signals]:
            try:
                signal = await self._ai_analyze_market(market)
                if signal and not signal.is_expired:
                    signals.append(signal)
            except Exception as e:
                print(f"[SignalPipeline] AI analyze error: {e}")
                continue

        return signals

    async def _ai_analyze_market(self, market: dict) -> Optional[SignalCard]:
        """Получить AI оценку одного рынка и создать SignalCard."""
        from services.polymarket import gamma
        yes_p, no_p = gamma.extract_prices(market)
        if yes_p <= 0:
            return None

        question = market.get("question", market.get("title", ""))
        volume = float(market.get("volume", 0) or 0)
        vol_24h = float(market.get("volume24hr", 0) or 0)
        cond_id = market.get("conditionId", market.get("id", ""))

        # Промпт для структурированного ответа
        prompt = f"""You are a prediction market analyst. Evaluate this market for trading signal.

Market: {question}
YES price: {yes_p:.0%}  NO price: {no_p:.0%}
Volume (24h): ${vol_24h:,.0f}  Total: ${volume:,.0f}

Respond with JSON only (no other text):
{{
  "direction": "YES" or "NO" or "SKIP",
  "fair_value": 0.XX,
  "confidence": 0.XX,
  "edge_pct": X.X,
  "reason": "one sentence why",
  "risk": "one sentence main risk",
  "priority": "HIGH" or "MEDIUM" or "LOW"
}}

Rules:
- direction=SKIP if no clear edge
- fair_value: your estimate of true probability
- edge_pct = abs(fair_value - current_price) / current_price * 100
- HIGH: edge > 10% and confidence > 0.75
- MEDIUM: edge > 5% and confidence > 0.60
- LOW: everything else"""

        try:
            timeout = aiohttp.ClientTimeout(total=20)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    json={
                        "model": AI_MODEL_FAST,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 200,
                        "temperature": 0.3,  # Низкая температура для структурированного ответа
                    },
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    ssl=False,
                ) as resp:
                    if resp.status != 200:
                        return None
                    data = await resp.json()
                    content = data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"[SignalPipeline] API error: {e}")
            return None

        # Парсим JSON
        try:
            # Убираем markdown обёртку если есть
            content = content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            result = json.loads(content)
        except Exception as e:
            print(f"[SignalPipeline] JSON parse error: {e}, content: {content[:100]}")
            return None

        direction = result.get("direction", "SKIP")
        if direction == "SKIP":
            return None

        fair_value = float(result.get("fair_value", yes_p))
        confidence = float(result.get("confidence", 0.5))
        edge_pct = float(result.get("edge_pct", 0))
        current_price = yes_p if direction == "YES" else no_p

        # Минимальный порог для сигнала
        if edge_pct < 3.0 or confidence < 0.50:
            return None

        priority = result.get("priority", "LOW")
        reason = result.get("reason", "AI model edge detected")
        risk = result.get("risk", "Market uncertainty")

        # Suggested amount: пропорционально edge и confidence
        base_amount = 10.0
        if priority == "HIGH":
            suggested = 25.0
        elif priority == "MEDIUM":
            suggested = 15.0
        else:
            suggested = 10.0

        end_date = (market.get("endDate") or "")[:10]

        return SignalCard(
            signal_id=f"ai_{cond_id}_{int(time.time())}",
            market_id=cond_id,
            question=question,
            direction=direction,
            current_price=current_price,
            fair_value=fair_value,
            edge_pct=edge_pct,
            confidence=confidence,
            source="ai_model",
            source_label="🤖 AI Model",
            reason=reason,
            risk=risk,
            priority=priority,
            suggested_amount=suggested,
            volume_24h=vol_24h,
            market_closes=end_date,
            token_id=cond_id,
        )

    # ── Источник 2: Whale Activity ────────────────────────────────────

    async def get_whale_signals(self, limit: int = 5) -> list[SignalCard]:
        """
        Мониторит крупные сделки через data-api.polymarket.com.
        Крупная сделка = >$5000 за последний час → сигнал направления.
        """
        signals = []
        try:
            session = await self._get_session()
            # Получаем недавние крупные сделки
            async with session.get(
                "https://data-api.polymarket.com/trades",
                params={"limit": 50, "taker_order_size": 1000},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status != 200:
                    return []
                trades = await resp.json()
                if not isinstance(trades, list):
                    trades = trades.get("trades", [])

            # Агрегируем по рынку
            market_flows: dict[str, dict] = {}
            for trade in trades:
                cid = trade.get("market", trade.get("conditionId", ""))
                if not cid:
                    continue
                size = float(trade.get("size", 0) or 0)
                side = trade.get("side", "").upper()  # BUY or SELL
                outcome = trade.get("outcome", "").upper()  # YES or NO

                if cid not in market_flows:
                    market_flows[cid] = {
                        "yes_buy": 0, "no_buy": 0, "total": 0,
                        "question": trade.get("title", ""),
                        "price": float(trade.get("price", 0.5) or 0.5),
                    }
                market_flows[cid]["total"] += size
                if outcome == "YES" and side == "BUY":
                    market_flows[cid]["yes_buy"] += size
                elif outcome == "NO" and side == "BUY":
                    market_flows[cid]["no_buy"] += size

            # Генерируем сигналы для рынков с явным потоком
            for cid, flow in market_flows.items():
                if flow["total"] < 1000:  # Минимум $1000 общего объёма
                    continue
                yes_flow = flow["yes_buy"]
                no_flow = flow["no_buy"]
                total = flow["total"]
                if total == 0:
                    continue

                imbalance = abs(yes_flow - no_flow) / total
                if imbalance < 0.3:  # Слабый сигнал — пропускаем
                    continue

                direction = "YES" if yes_flow > no_flow else "NO"
                current_price = flow["price"]
                question = flow["question"] or cid[:20]

                # Приоритет по размеру потока
                if total > 10000:
                    priority = "HIGH"
                    suggested = 25.0
                elif total > 5000:
                    priority = "MEDIUM"
                    suggested = 15.0
                else:
                    priority = "LOW"
                    suggested = 10.0

                # Только HIGH/MEDIUM сигналы от whales
                if priority == "LOW":
                    continue

                signals.append(SignalCard(
                    signal_id=f"whale_{cid}_{int(time.time())}",
                    market_id=cid,
                    question=question,
                    direction=direction,
                    current_price=current_price,
                    fair_value=current_price * 1.05 if direction == "YES" else current_price * 0.95,
                    edge_pct=5.0,
                    confidence=0.65,
                    source="whale_activity",
                    source_label="🐋 Whale Activity",
                    reason=f"${total:,.0f} in {direction} buys in last hour",
                    risk="Whale may have information advantage or be wrong",
                    priority=priority,
                    suggested_amount=suggested,
                    volume_24h=total,
                    token_id=cid,
                ))

                if len(signals) >= limit:
                    break

        except Exception as e:
            print(f"[SignalPipeline] Whale signals error: {e}")

        return signals

    # ── Агрегация и фильтрация ────────────────────────────────────────

    @classmethod
    def _prioritize(cls, signals: list[SignalCard]) -> list[SignalCard]:
        """Сортировка: HIGH > MEDIUM > LOW, внутри — по edge_pct."""
        priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        return sorted(
            signals,
            key=lambda s: (priority_order.get(s.priority, 3), -s.edge_pct)
        )

    @classmethod
    def _deduplicate(cls, signals: list[SignalCard]) -> list[SignalCard]:
        """Убрать дубликаты по market_id."""
        seen = set()
        result = []
        for s in signals:
            if s.market_id not in seen:
                seen.add(s.market_id)
                result.append(s)
        return result

    async def get_feed(
        self,
        markets: list[dict],
        max_signals: int = 7,
        include_whales: bool = True,
    ) -> list[SignalCard]:
        """
        Получить агрегированный фид сигналов.
        Используется Intel Mode (handlers/intel.py).

        Args:
            markets: список рынков от Gamma API
            max_signals: максимум сигналов в фиде
            include_whales: добавлять whale сигналы

        Returns:
            Список SignalCard, отсортированных по приоритету
        """
        # Проверяем кеш
        if (
            SignalPipeline._cache
            and (time.time() - SignalPipeline._cache_time) < SignalPipeline._cache_ttl
        ):
            return SignalPipeline._cache[:max_signals]

        # Параллельная генерация из источников
        tasks = [self.generate_ai_signals(markets, max_signals=5)]
        if include_whales:
            tasks.append(self.get_whale_signals(limit=3))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_signals: list[SignalCard] = []
        for r in results:
            if isinstance(r, list):
                all_signals.extend(r)
            elif isinstance(r, Exception):
                print(f"[SignalPipeline] Source error: {r}")

        # Фильтрация просроченных
        all_signals = [s for s in all_signals if not s.is_expired]

        # Дедупликация + приоритизация
        all_signals = self._deduplicate(all_signals)
        all_signals = self._prioritize(all_signals)

        # Обновляем кеш
        SignalPipeline._cache = all_signals
        SignalPipeline._cache_time = time.time()

        return all_signals[:max_signals]

    def clear_cache(self):
        """Очистить кеш (вызывается при принудительном обновлении)."""
        SignalPipeline._cache = []
        SignalPipeline._cache_time = 0


# Глобальный экземпляр
signal_pipeline = SignalPipeline()
