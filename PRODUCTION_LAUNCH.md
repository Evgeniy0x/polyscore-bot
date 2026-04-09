# PolyScore — Production Launch Reference

## Статус
- ✅ Бот запущен (demo режим)
- ✅ Intel Feed работает
- ✅ Торговый UX готов
- ✅ Demo/Real разделены явно (нет silent fallback)
- ✅ Правильный token_id для CLOB
- ✅ py-clob-client добавлен в requirements.txt
- ⏳ Ждём: Polymarket API ключи + приватный ключ кошелька

## Для запуска real trading нужно 4 вещи

1. `POLY_API_KEY` — Builder API key с polymarket.com
2. `POLY_SECRET` — Builder API secret
3. `POLY_PASSPHRASE` — Builder API passphrase
4. `POLY_PRIVATE_KEY` — приватный ключ Polygon-кошелька (для подписи ордеров)

## Как установить

```bash
# Отредактируй setup_secrets.sh — вставь ключи
nano setup_secrets.sh

# Запусти — создаст .env
bash setup_secrets.sh

# Установи py-clob-client
pip install py-clob-client

# Перезапусти бота
python fix_and_run.py
```

## Где получить ключи

**Polymarket Builder API:**
→ https://polymarket.com/settings?tab=builder
→ Войди → "Create API Key" → скопируй Key, Secret, Passphrase

**POLY_PRIVATE_KEY:**
→ Это приватный ключ Polygon-кошелька из которого будут идти ордера
→ MetaMask: Аккаунт → три точки → "Export Private Key"
→ Начинается с 0x, длина 66 символов

**Пополнение кошелька USDC:**
→ Биржа (Binance/Bybit) → Вывод → USDC → Сеть: Polygon (MATIC)
→ Адрес: тот что в /wallet в боте

## Smoke test после настройки

1. `python fix_and_run.py`
2. Открыть бота в Telegram
3. Сделать ставку $1 на любой рынок
4. Убедиться что показывает "✅ Trade opened" + Order ID (не "DEMO")
5. Проверить на polymarket.com что ордер появился
