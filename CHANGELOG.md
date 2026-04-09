# PolyScore — История изменений и действий

## 21.03.2026 — Стратегический разворот: AutoTrade + Копитрейдинг

### Новая бизнес-модель (принято решение)
- ✅ Отказались от модели "информационный бот + Builder Fee как основной доход"
- ✅ Новая стратегия: Путь 2 (собственный торговый алгоритм) + Путь 3 (копитрейдинг)
- ✅ Монетизация: 20% от прибыли пользователей копитрейдинга + прибыль собственного алгоритма
- ✅ Builder Fee остаётся как дополнительный бонус

### Торговый алгоритм (services/trading_algorithm.py — НОВЫЙ ФАЙЛ)
- ✅ Стратегия 1: Sum-to-One арбитраж (YES + NO < $0.97 → покупаем оба)
- ✅ Стратегия 2: Логический арбитраж между связанными рынками (Trump/Republican, BTC/crypto и т.д.)
- ✅ Риск-менеджер: максимальная позиция, дневной лимит убытков, лимит сделок
- ✅ Режим PAPER (симуляция) и LIVE (реальные ордера через CLOB API)
- ✅ Интеграция с py-clob-client (официальный клиент Polymarket)
- ✅ Builder API Key встроен в заголовки запросов
- ✅ Стартовый капитал: $1,000

### Бот (handlers/start.py — ПЕРЕПИСАН)
- ✅ Новый welcome screen: AutoTrading вместо "Ставки на спорт"
- ✅ Главное меню: кнопка "AutoTrade — бот за меня" на первом месте
- ✅ Обновлён оффер на всех 12 языках
- ✅ Объём Polymarket обновлён: $7B → $22B (актуальные данные 2025)

### Лендинг (index.html — ОБНОВЛЁН)
- ✅ Новый title: "AutoTrading on Polymarket | Official Builder"
- ✅ Новый H1: "AutoTrading / on Polymarket / Bot earns for you"
- ✅ Обновлена hero-подпись: алгоритм 24/7, 20% только с прибыли
- ✅ Статы обновлены: "0%" → "20%", "$7B" → "$22B", "AES-256" → "24/7"
- ✅ Бегущая строка обновлена: Zero Fees → AutoTrade 24/7
- ✅ SEO мета-теги обновлены под AutoTrading

---

## 21.03.2026 — День активного запуска

### Polymarket Builder Program
- ✅ Создан аккаунт Builder на polymarket.com/settings?tab=builder
- ✅ Builder Address: `0x9d0724d90f6f3ea13990afd3b7211ff358efc489`
- ✅ Builder API Key создан: `019d0c95-6adc-764f-9dd1-d79e70e3f1fe`
- ✅ Заявка подана на builders.polymarket.com
- ✅ Письмо отправлено на builders@polymarket.com в 18:46

### Лендинг (polyscore-bot.vercel.app)
- ✅ Полный редизайн в стиле Polymarket (тёмный фон, зелёные акценты)
- ✅ Мобильная версия — полный responsive CSS для iPhone и Android
- ✅ Исправлен баг с градиентным текстом на Safari (зелёные прямоугольники)
- ✅ Бейджи "Polymarket Builder" и "Live on Telegram" выровнены
- ✅ Canvas-анимация с блокчейн данными (hex-адреса, цены, спарклайны)
- ✅ Плавающие фигуры скрыты на мобильном (оптимизация)
- ✅ Поддержка Dynamic Island / notch (safe-area-inset)
- ✅ Таблица сравнения с горизонтальным скроллом на мобильном
- ✅ Ссылки на бот обновлены: @PolymarketMAMA_Bot везде

### Коммиты на GitHub (main branch)
| Коммит | Описание |
|--------|----------|
| `eff1350` | Full Polymarket brand style |
| `2b96810` | Badges same height, clean coin shapes |
| `0d5b14a` | Badges exact same height 32px |
| `6f721f6` | Badges lower + blockchain canvas |
| `dac7545` | Push badges down 96px from navbar |
| `45d6351` | Full mobile responsive CSS |
| `1bdb7de` | Safari gradient text fix, canvas hidden on mobile |

---

## TODO — Следующие шаги

### Критически важно (сделать первым)
- [ ] Вшить Builder API Key `019d0c95-6adc-764f-9dd1-d79e70e3f1fe` в код бота
  - Найти в коде место где отправляются ордера на Polymarket CLOB
  - Добавить заголовок: `POLY-BUILDER: 019d0c95-6adc-764f-9dd1-d79e70e3f1fe`
  - Без этого Polymarket не атрибутирует сделки и не платит USDC
- [ ] Получить статус Verified Builder (ответ от Polymarket на письмо)
- [ ] Дождаться ответа от builders@polymarket.com

### Сайт
- [ ] Купить домен — рекомендуется polyscore.trade ($27/год) или polyscore.io ($38/год)
- [ ] Подключить домен к Vercel
- [ ] Добавить Privacy Policy страницу
- [ ] Добавить Terms of Service страницу
- [ ] Подключить Google Analytics / Mixpanel

### Монетизация
- [ ] Builder API Key в коде бота → атрибуция сделок → еженедельные USDC
- [ ] Настроить кошелёк для получения USDC от Polymarket
- [ ] Юридическое оформление (ИП или LLC)

### Продукт
- [ ] Криптовалютные рынки (BTC/ETH, altcoins)
- [ ] 15-минутные микро-рынки
- [ ] PolyScore AI (анализ Twitter/X + on-chain данных)
- [ ] Реальные цифры пользователей для следующего письма в Polymarket

---

## Конкуренты

| Бот | Комиссия | Языки | Академия | Статус |
|-----|----------|-------|----------|--------|
| **PolyScore** | **0%** | **12** | **✅** | **Активен** |
| PolyGun | +1% | EN only | ❌ | Активен |
| PolyCop | +0.5% | EN only | ❌ | Активен |
| PolyBot | +1% | EN only | ❌ | Активен |
| Polycule | +1% | EN only | ❌ | Взломан $230K, офлайн |

---

## Ключевые данные проекта

```
Бот:              @PolymarketMAMA_Bot (t.me/PolymarketMAMA_Bot)
Лендинг:          https://polyscore-bot.vercel.app
GitHub:           https://github.com/Evgeniy0x/polyscore-bot
Builder Address:  0x9d0724d90f6f3ea13990afd3b7211ff358efc489
Builder API Key:  019d0c95-6adc-764f-9dd1-d79e70e3f1fe
Email:            nomer5555@gmail.com
Верификация:      Pending (заявка подана 21.03.2026)
Деплой:           Vercel (лендинг) + Railway (бот)
```
