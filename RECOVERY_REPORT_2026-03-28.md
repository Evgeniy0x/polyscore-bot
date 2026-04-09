# Аварийное восстановление ботов — 28.03.2026

## Причина

Telegram-аккаунт MARiO (@Mario_Lalala) был удалён/пересоздан Telegram. Все 4 бота привязанные к аккаунту уничтожены. Потребовалось создать новых ботов через BotFather и заменить токены во всех системах.

---

## Реестр ботов

| Бот | Username | Новый токен | Старый токен | Статус |
|-----|----------|-------------|--------------|--------|
| Valli CEO | @VallyCEO_bot | `8656520622:AAEq...` | `8723074289:AAHo...` | Работает |
| ГРАФИТ | @Grafit35_bot | `8745495960:AAFX...` | `8783535414:AAFN...` | Работает (VPS) |
| Личный Секретарь Джарвис | @secretar35_bot | `8768261506:AAHF...` | `8255940975:AAEI...` | Работает |
| PolyScore | @PolymarketMAMA_Bot | `8344715524:AAFD...` | `8665148588:AAHT...` | Работает |

---

## Что было сделано

### 1. Valli CEO (@VallyCEO_bot)
- Создан новый бот в BotFather
- Токен заменён в конфигурации на Mac Mini
- Notion: обновлена страница "Регламенты работы"

### 2. ГРАФИТ (@Grafit35_bot)
- Создан новый бот в BotFather
- Токен заменён на VPS (5.42.126.58): `/root/grafit-fuel-bot/.env`
- Сервис перезапущен: `systemctl restart grafit-bot`
- Исправлена ошибка `ImportError: CustomerOut` в `schemas.py` (добавлены алиасы)
- Notion: обновлена страница "Grafit — Ключи и токены"

### 3. Личный Секретарь Джарвис (@secretar35_bot)
- Создан новый бот в BotFather, переименован из "Секретарь"
- Токен заменён в двух `.env` файлах:
  - `~/ПРОЕКТЫ/jarvis-agent/.env`
  - `~/ПРОЕКТЫ/openclaw-ai/.env`
- Исправлена критическая ошибка совместимости Python 3.14:
  - `asyncio.get_event_loop()` больше не работает в MainThread
  - Заменён `app.run_polling()` на ручное управление event loop
- Установлена недостающая зависимость: `python-telegram-bot[job-queue]`

### 4. PolyScore (@PolymarketMAMA_Bot)
- Токен заменён в `.env`, `config.py`, `setup_secrets.sh`
- Исправлена ошибка "not enough balance / allowance":
  - Создан `approve_polygon.py` — on-chain approve USDC + CTF на контракты Polymarket
  - Выполнены approve-транзакции на Polygon mainnet (кошелёк `0x02659D56...`)
  - Создан `cancel_orders.py` — отмена висящих ордеров, блокирующих баланс
- Исправлена логика продажи в `handlers/betting.py`:
  - Убраны нерабочие вызовы Relayer approve (только для Safe-кошельков)
  - Продажа теперь использует best bid из orderbook вместо лимитного ордера по текущей цене

---

## Blockchain-операции (Polygon)

Кошелёк: `0x02659D56e31be224D689953397eFA80D61A039D4`

Выполненные approve-транзакции:

| Контракт | Токен | Статус |
|----------|-------|--------|
| CTF Exchange | USDC Native | Approved |
| CTF Exchange | USDC.e | Approved |
| CTF Exchange | CTF | Approved |
| Neg Risk Exchange | USDC Native | Approved |
| Neg Risk Exchange | CTF | Approved |
| Neg Risk Adapter | USDC Native | Approved |
| Neg Risk Adapter | CTF | Approved |

---

## Notion — обновлённые страницы

1. **"Grafit — Ключи и токены"** — новый токен ГРАФИТ
2. **"Регламенты работы"** — новый токен Valli CEO

---

## Оставшееся действие (ручное)

### Обновить токен в valli-telegram/SKILL.md

Файл read-only из Cowork. Выполнить на Mac Mini:

```bash
sed -i '' 's/8723074289:AAHoTqng0ToeU-t6UYAd-wfBUh_XxkYtsAA/8656520622:AAEqHDphifvG5Jvj8SYpOMQ4tr5e02Qox2E/g' ~/path/to/valli-telegram/SKILL.md
```

Путь к SKILL.md нужно уточнить — это файл скилла Claude Code для Valli.

---

## Инфраструктура

| Компонент | Где работает | Путь |
|-----------|-------------|------|
| Valli CEO | Mac Mini | ~/valli-company/ |
| ГРАФИТ | VPS 5.42.126.58 | /root/grafit-fuel-bot/ |
| Секретарь/Джарвис | Mac Mini | ~/ПРОЕКТЫ/openclaw-ai/ |
| PolyScore | Mac Mini | ~/Documents/Claude/Scheduled/polyscore-bot/ |
