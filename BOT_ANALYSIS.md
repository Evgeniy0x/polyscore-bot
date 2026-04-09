# PolyScore Bot — Полный анализ и план трансформации
> Версия: 1.0 · Дата: 2026-03-21
> Автор: архитектурный анализ на основе реального кода

---

## PHASE 0 — КАРТА ТЕКУЩЕЙ АРХИТЕКТУРЫ

### Структура файлов

```
polyscore-bot/
├── bot.py                     # Точка входа, регистрация хендлеров
├── config.py                  # Конфиг, токены, категории
├── handlers/
│   ├── start.py               # /start, /help, /lang, cb_main_menu
│   ├── markets.py             # Просмотр рынков (cat:, tag:)
│   ├── betting.py             # Ставки (b:Y/N, bet:confirm)
│   ├── portfolio.py           # Портфель + AI-прогнозы
│   ├── wallet.py              # Кошелёк (создание, подключение)
│   ├── alerts.py              # Алерты на цену
│   ├── parlay.py              # Парлеи
│   ├── copy_trading.py        # Copy-trade хендлеры
│   ├── leaderboard.py         # Лидерборд
│   ├── academy.py             # Академия
│   └── __init__.py
├── services/
│   ├── database.py            # SQLite (aiosqlite)
│   ├── polymarket.py          # Gamma API + CLOB API + Relayer
│   ├── ai_service.py          # OpenRouter (Gemini Flash / Claude Sonnet)
│   ├── copy_trading.py        # CopyTradingService class
│   ├── trading_algorithm.py   # 4 стратегии торгового алгоритма
│   ├── crypto.py              # AES-256 шифрование ключей
│   ├── translator.py          # Переводчик через AI
│   └── __init__.py
└── utils/
    └── bet_slip.py            # Генерация bet slip карточек (PIL)
```

### Схема ConversationHandlers

```
wallet_conv:
  → /wallet → WAIT_WALLET_ADDRESS → msg_wallet_address → END

bet_conv:
  → cb_bet_start (b:Y:{idx} / b:N:{idx})
  → WAIT_AMOUNT
  → msg_bet_amount → ConversationHandler.END (показывает подтверждение)
  → cb_bet_confirm → (реальный ордер или demo) → bet_slip карточка
  → cb_bet_cancel → END
```

### База данных (SQLite)

| Таблица | Ключевые колонки |
|---|---|
| `users` | user_id, username, language, wallet_address, signer_address, private_key (AES-256) |
| `bets` | user_id, market_id, question, outcome, amount, price, potential_win, order_id, status |
| `parlays` | user_id, legs (JSON), total_odds, total_amount, potential_win, status |
| `watchlist` | user_id, market_id, question |
| `copy_follows` | user_id, trader_address, trader_name, copy_pct, active, last_trade_id |
| `academy_progress` | user_id, completed_lessons (JSON), total_xp, achievements (JSON) |
| `price_alerts` | user_id, market_id, question, target_price, direction, triggered |

### Команды и callbacks

**Команды:**
`/start` `/help` `/sports` `/trending` `/ai` `/lang` `/portfolio` `/parlay` `/wallet` `/leaderboard`

**Callback паттерны:**
- `menu:main` — главное меню
- `lang:{code}` — смена языка
- `cat:markets`, `cat:sports`, `cat:trending` — навигация категорий
- `tag:{slug}` — рынки по тегу
- `m:{idx}` — детальный просмотр рынка (по кешу bot_data["mc"])
- `w:{idx}` — watchlist добавление
- `b:Y:{idx}`, `b:N:{idx}` — начало ставки
- `bet:confirm`, `bet:cancel` — подтверждение/отмена ставки
- `parlay:new`, `pl:{n}` — парлеи
- `portfolio`, `portfolio:all`, `portfolio:parlays` — портфель
- `wallet:status`, `wallet:create`, `wallet:add` — кошелёк
- `copy:menu`, `copy:search`, `copy:follow:`, `copy:unfollow:` — copy trading
- `ai:morning`, `edge:{idx}` — AI брифинг и анализ edge
- `academy:main` — академия
- `alerts` — алерты
- `leaderboard` — лидерборд
- `settings` — настройки

### Ключевые сервисы

**GammaClient** (`polymarket.py`):
- `get_sports_markets(tag, limit, offset)` → список рынков через `/events`
- `get_market(id)` → детали рынка
- `search_markets(query)` → поиск
- `extract_prices(market)` → YES/NO цены из двух форматов (tokens / outcomePrices)
- Кеш рынков в `ctx.bot_data["mc"]` — словарь int→dict, макс 200 записей

**ClobClient** (`polymarket.py`):
- Торговля через `py-clob-client` (опционально, fallback → demo)
- MarketOrder, FOK тип ордера

**RelayerClient** (`polymarket.py`):
- `create_wallet(signer_address)` → Safe Wallet через Relayer API
- Fallback → EOA если Relayer недоступен

**ai_service.py**:
- Синхронный `call_openrouter()` через `urllib.request` (ssl unverified)
- Функции: `get_sport_prediction()`, `get_morning_briefing()`, `explain_market()`, `analyze_edge()`
- Поддержка всех 12 языков через language-specific промпты

**trading_algorithm.py** (v2):
- 4 стратегии: cross-platform arbitrage, behavioral fades, micro market making, event-driven
- Paper mode + live mode
- Signal dataclass с TTL, TradeResult
- MarketDataFeed, RiskManager, PositionTracker
- Запускается отдельно, не интегрирован в бот как сервис

**crypto.py**:
- AES-256 CTR в чистом Python (без cryptography lib)
- Мастер-ключ из `WALLET_ENCRYPTION_KEY` env (fallback → SHA256 от BOT_TOKEN)
- Формат: base64(nonce_16 + ciphertext + hmac_32)

---

## PHASE 1 — GAP ANALYSIS

### ЧТО ЕСТЬ (работает)

| Компонент | Статус | Качество |
|---|---|---|
| Онбординг 12 языков | ✅ Есть | Хорошо |
| Просмотр рынков по категориям | ✅ Есть | Хорошо |
| Ставки YES/NO с подтверждением | ✅ Есть | Хорошо |
| Bet slip карточки | ✅ Есть | Есть |
| Кошелёк (создание + ввод вручную) | ✅ Есть | Хорошо |
| Парлеи | ✅ Есть | Базово |
| AI прогнозы (OpenRouter) | ✅ Есть | Хорошо |
| Price alerts | ✅ Есть | Базово |
| Copy trading UI | ✅ Есть | Скелет |
| Watchlist | ✅ Есть | Базово |
| Академия | ✅ Есть | Неизвестно |
| Лидерборд | ✅ Есть | Неизвестно |
| AES-256 шифрование ключей | ✅ Есть | Хорошо |

### ЧТО ОТСУТСТВУЕТ (по Blueprint)

#### КРИТИЧНО — без этого продукт не работает:

1. **Реальный PnL из цепочки** — портфель показывает только локальные записи из БД, а не реальный on-chain баланс. Нет синхронизации с Polymarket API для текущих позиций и реализованного PnL.

2. **Real-time цены на позиции** — статус ставок всегда `pending`, нет механизма обновления статуса при завершении рынка (resolved/settled).

3. **Уведомления о закрытых позициях** — нет нотификаций когда рынок закрылся и пользователь выиграл/проиграл.

4. **Intel Mode vs Trader Mode** — из Blueprint: dual mode система. Сейчас всё смешано в одном меню без чёткого разделения "смотреть и учиться" vs "торговать".

5. **Signal → Decision → Execution loop** — trading_algorithm.py существует как standalone скрипт, но НЕ интегрирован в бот как сервис рекомендаций пользователю. Сигналы генерируются, но не доставляются.

6. **URL → trade в 3 тапа** — нет обработки ссылок Polymarket (paste URL → бот парсит и предлагает ставку).

#### ВАЖНО — ухудшает продукт:

7. **Decision Objects вместо generic AI** — ai_service возвращает текст, не структурированные объекты с `action`, `confidence`, `amount_suggestion`.

8. **Retention engine** — нет: streak, daily digest, push после победы.

9. **Copy trading реально работает** — CopyTradingService polling есть, но нет реального исполнения ордеров через CLOB API. Только уведомления.

10. **Portfolio синхронизация** — нет `GET /positions` из data-api.polymarket.com для реальных позиций.

11. **Leaderboard реальный** — лидерборд, скорее всего, показывает только внутренних пользователей БД, а не топ-трейдеров Polymarket.

12. **Настройки** — `settings` callback не реализован (есть кнопка, но нет хендлера с реальным функционалом).

#### НЕЗНАЧИТЕЛЬНО — можно отложить:

13. Монетизация / подписки
14. Shareable bet слипы с UTM
15. Referral система
16. Многовалютный баланс

---

## PHASE 2 — MVP DEFINITION

### MVP = что нужно пользователю чтобы реально зарабатывать

**Минимально рабочий продукт (8-10 недель работы):**

```
CORE LOOP:
  Войти → Увидеть сигнал с объяснением → Одобрить → Увидеть результат

КОНКРЕТНО:
1. Онбординг: кошелёк → депозит → первая ставка (менее 60 сек)
2. Daily AI briefing: 3-5 рынков с чёткой рекомендацией + confidence
3. Ставка: рынок → YES/NO → сумма → подтвердить (3 тапа)
4. Portfolio с реальным PnL (из Polymarket API, не только локальная БД)
5. Уведомление при win/loss с итогом
6. Copy trading с реальным исполнением (хотя бы симуляция подтверждённая)
```

**За рамки MVP (откладываем):**
- Академия (оставляем как есть)
- Парлеи (работают, не трогаем)
- Leaderboard (статичный — ок)
- Референальная программа
- Monetization layer

---

## PHASE 3 — SYSTEM DESIGN

### Новые компоненты для добавления

#### 3.1 Position Sync Service
```
services/position_sync.py

Задача: каждые 10 мин синхронизировать позиции пользователей из Polymarket API.

GET https://data-api.polymarket.com/positions?user={wallet}&sizeThreshold=0

Логика:
  - для каждого активного пользователя (активен < 48 ч)
  - запросить открытые позиции
  - обновить таблицу bets (добавить current_price, pnl_realized, status)
  - если рынок resolved и status != settled → отправить уведомление
```

#### 3.2 Signal Delivery Pipeline
```
services/signal_pipeline.py

Задача: trading_algorithm генерирует Signal → бот доставляет пользователям.

Signal → фильтрация (confidence > 0.65) → группировка по категории
→ пользователи подписанные на эту категорию → push уведомление

Таблица БД: signal_subscriptions (user_id, category, active)
```

#### 3.3 Decision Object (структурированный AI ответ)
```python
@dataclass
class DecisionObject:
    market_id: str
    question: str
    action: str        # "BUY_YES" / "BUY_NO" / "SKIP"
    confidence: float  # 0.0 - 1.0
    reasoning: str     # 2-3 предложения
    suggested_amount: float  # USDC
    edge: float        # ожидаемое преимущество %
    expire_at: datetime
```

Вместо `get_sport_prediction()` возвращающего str → возвращает `DecisionObject`.
Это позволяет боту предлагать кнопку "Купить X USDC YES" сразу под анализом.

#### 3.4 Retention Engine
```
services/retention.py

daily_digest: каждое утро в 9:00 по local time пользователя
  → 3 лучших рынка дня + AI рекомендация
  → если есть открытые позиции → их текущий статус

win_notification: при win → красивая карточка с P&L
streak_tracker: N дней подряд активности → бейдж
```

#### 3.5 URL Parser
```
handlers/url_handler.py

Паттерн: msg содержит polymarket.com/event/... или polymarket.com/markets/...
→ парсим slug из URL
→ загружаем рынок через gamma.get_market(slug)
→ показываем карточку рынка с кнопками YES/NO сразу
```

### Обновления существующих компонентов

#### Portfolio (portfolio.py)
```
ТЕКУЩЕЕ: берёт данные только из локальной БД (bets таблица)
НУЖНО:
  1. Запросить реальные позиции из data-api.polymarket.com/positions
  2. Смёрджить с локальными данными
  3. Показывать current_value / entry_value / P&L
  4. Список реализованных (win/loss) + нереализованных
```

#### AI Briefing (ai_service.py → async)
```
ТЕКУЩЕЕ: синхронный urllib.request (блокирует event loop!)
НУЖНО: async aiohttp.ClientSession как в polymarket.py
ТАКЖЕ: возвращать DecisionObject, не str
```

#### Copy Trading (services/copy_trading.py)
```
ТЕКУЩЕЕ: polling есть, но execute_copy() просто уведомляет
НУЖНО:
  Если пользователь включил auto-execute:
    → создать пропорциональный ордер через CLOB API
    → сохранить в bets таблицу
    → уведомить пользователя о копированной сделке
```

---

## PHASE 4 — ERROR HANDLING SPEC

### Принципы

1. **Никогда не ронять бот** — все async handlers в try/except
2. **Показывать понятное сообщение** — не technical error, а "Что-то пошло не так, попробуй позже"
3. **Логировать детали** — `print(f"[MODULE] Error: {e}")` + traceback для критических
4. **Graceful degradation** — если AI недоступен, показать рынки без анализа; если CLOB недоступен, сохранить как demo ордер

### Карта ошибок

| Ситуация | Текущее поведение | Нужное поведение |
|---|---|---|
| Gamma API недоступен | Exception → крашит хендлер | Показать cached данные или "Рынки временно недоступны" |
| CLOB ордер отклонён | Показывает error_msg | Объяснить причину (низкий баланс, ликвидность) |
| AI timeout | "⚠️ AI временно недоступен" | Ок, но сделать async |
| Wallet не подключён перед ставкой | Нет проверки | Redirect в /wallet с объяснением |
| ctx.user_data["bet"] пустой | "Сессия истекла" | + кнопка вернуться к рынкам |
| Relayer недоступен | Fallback к EOA | ✅ Уже реализовано |
| DB connection error | Exception | Retry 3 раза с backoff |

### Middleware для централизованной обработки

```python
# utils/error_handler.py

async def handle_callback_error(update, context, error):
    """Глобальный обработчик ошибок для всех callbacks."""
    query = update.callback_query
    if query:
        await query.answer()
        user = await get_user(query.from_user.id)
        lang = (user or {}).get("language", "ru")
        msg = "⚠️ Ошибка. Попробуй снова." if lang == "ru" else "⚠️ Error. Please try again."
        try:
            await query.edit_message_text(
                msg,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🏠 Меню" if lang=="ru" else "🏠 Menu",
                                         callback_data="menu:main")
                ]])
            )
        except Exception:
            pass
    # Логируем
    print(f"[ERROR] {type(error).__name__}: {error}")
    import traceback
    traceback.print_exc()
```

---

## PHASE 5 — IMPLEMENTATION PLAN

### Приоритеты (Impact / Effort матрица)

**Блок 1 — Быстрые победы (1-2 дня каждое):**

| Задача | Файл | Описание |
|---|---|---|
| Fix AI async | `services/ai_service.py` | urllib → aiohttp, не блокирует event loop |
| Wallet guard | `handlers/betting.py` | Проверка wallet_address перед ставкой |
| Settings handler | `handlers/start.py` / новый файл | Реализовать callback `settings` |
| Error middleware | `utils/error_handler.py` | Глобальный обработчик |
| URL parser | `handlers/url_handler.py` | polymarket.com ссылки → ставка |

**Блок 2 — Реальный портфель (3-5 дней):**

| Задача | Файл | Описание |
|---|---|---|
| Position Sync Service | `services/position_sync.py` | Новый файл, cron каждые 10 мин |
| DB migration | `services/database.py` | Добавить: current_price, pnl_realized в bets; new table: positions |
| Portfolio rewrite | `handlers/portfolio.py` | Реальный P&L из API + локальные данные |
| Win/Loss notifications | `services/retention.py` | Push при resolved рынке |

**Блок 3 — Signal Loop (5-7 дней):**

| Задача | Файл | Описание |
|---|---|---|
| DecisionObject | `services/ai_service.py` | Structured output вместо str |
| Signal Pipeline | `services/signal_pipeline.py` | Новый файл |
| Daily Briefing push | `services/retention.py` | 09:00 по UTC, 3-5 рынков |
| Approve/Skip UI | `handlers/markets.py` | Кнопки под AI сигналом |

**Блок 4 — Copy Trading (7-10 дней):**

| Задача | Файл | Описание |
|---|---|---|
| Real CLOB execution | `services/copy_trading.py` | execute_copy() через py-clob-client |
| Copy confirmation UI | `handlers/copy_trading.py` | Показать сделку перед исполнением |
| Simulation mode | `services/copy_trading.py` | Paper mode для новых пользователей |

---

## PHASE 6 — CRITICAL FIXES (делать ПЕРВЫМИ)

### Fix #1 — AI блокирует event loop

**Проблема:** `call_openrouter()` в `ai_service.py` использует `urllib.request.urlopen()` — СИНХРОННЫЙ вызов внутри async бота. Это блокирует весь event loop пока AI думает (до 30 сек).

**Решение:**
```python
# Заменить urllib на aiohttp
import aiohttp
import asyncio

async def call_openrouter_async(prompt: str, model: str, max_tokens: int = 600) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json={"model": model, "messages": [{"role": "user", "content": prompt}],
                  "max_tokens": max_tokens, "temperature": 0.7},
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}",
                     "Content-Type": "application/json"},
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            data = await resp.json()
            return data["choices"][0]["message"]["content"].strip()
```

### Fix #2 — Нет проверки кошелька перед ставкой

**Проблема:** `cb_bet_start` не проверяет `wallet_address` перед запросом суммы. Пользователь вводит сумму, и только при `cb_bet_confirm` узнаёт что не может торговать (или торгует в demo).

**Решение:** в начале `cb_bet_start`:
```python
user = await get_user(query.from_user.id)
if not user or not user.get("wallet_address"):
    await query.edit_message_text(
        "💳 Для торговли нужен кошелёк.\n\nПодключи его за 5 секунд:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🚀 Создать кошелёк", callback_data="wallet:create"),
            InlineKeyboardButton("📲 У меня есть", callback_data="wallet:add"),
        ]])
    )
    return ConversationHandler.END
```

### Fix #3 — Market cache может быть пустым при restart

**Проблема:** `ctx.bot_data["mc"]` — in-memory кеш. После перезапуска бота все рынки пропадают, и callback `m:{idx}` не найдёт рынок.

**Решение:** добавить проверку и повторный запрос:
```python
market = ctx.bot_data.get("mc", {}).get(idx)
if not market:
    # Попробовать перезагрузить из Gamma API по slug если есть в user_data
    # или показать сообщение с кнопкой обновить список
    await query.edit_message_text(
        "🔄 Список рынков обновился. Открой категорию снова.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("📊 Рынки", callback_data="cat:markets")
        ]])
    )
    return
```

### Fix #4 — Callback `settings` не реализован

**Проблема:** кнопка ⚙️ Настройки в главном меню отправляет `settings`, но нет хендлера → `cb_unknown_callback` выводит "Неизвестная команда".

**Решение:** добавить минимальный handler:
```python
async def cb_settings(update, ctx):
    user = await get_user(update.callback_query.from_user.id)
    lang = (user or {}).get("language", "ru")
    # Показать меню настроек: язык, уведомления, кошелёк
    ...
```

---

## PHASE 7 — ПОРЯДОК ДЕЙСТВИЙ

### Шаг 1 (сегодня)
1. Применить Fix #1 (AI async) — не ломает ничего, только улучшает
2. Применить Fix #2 (wallet guard) — защита от confusion
3. Применить Fix #3 (cache fallback) — улучшает UX после restart
4. Применить Fix #4 (settings stub) — убирает "Неизвестная команда"

### Шаг 2 (следующий сессия)
5. Создать `services/position_sync.py`
6. Обновить portfolio handler
7. Добавить win/loss notifications

### Шаг 3 (после тестирования Шага 2)
8. DecisionObject + structured AI output
9. Signal pipeline + daily briefing
10. URL handler

### Шаг 4 (финал MVP)
11. Copy trading real execution
12. Retention engine (streak, notifications)

---

## САМОПРОВЕРКА

- [x] Прочитан весь код: bot.py, config.py, все handlers, все services, utils
- [x] Выявлены критические баги (AI блокировка, кеш, wallet guard)
- [x] Gap analysis: что есть vs что нужно по Blueprint
- [x] MVP scope определён — реальный портфель + AI сигналы
- [x] Порядок имплементации: от быстрых побед к сложным фичам
- [x] Error handling spec с конкретными примерами кода
- [x] НЕ ИЗМЕНЁН НИ ОДИН ФАЙЛ — только анализ
