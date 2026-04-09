#!/bin/bash
# PolyScore — Настройка секретов для production
# Заполни значения ниже, затем запусти: bash setup_secrets.sh
# Это создаст файл .env в папке с ботом.

# ─── ЗАПОЛНИ ЭТИ ЗНАЧЕНИЯ ──────────────────────────────────────────────────────

# 1. BOT_TOKEN — вставь свой токен сюда
BOT_TOKEN=""              # ← вставь сюда

# 2. OpenRouter API Key
OPENROUTER_API_KEY=""     # ← вставь сюда

# 3. Polymarket Builder API (получить на polymarket.com/settings?tab=builder)
POLY_API_KEY=""         # ← вставь сюда
POLY_SECRET=""          # ← вставь сюда
POLY_PASSPHRASE=""      # ← вставь сюда

# 4. Приватный ключ торгового кошелька Polygon (нужен для подписи ордеров)
POLY_PRIVATE_KEY=""     # ← вставь сюда (формат: 0x...)

# 5. Ключ шифрования кошельков пользователей в БД
# Если пустой — генерируется автоматически ниже

# ────────────────────────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

# Генерируем WALLET_ENCRYPTION_KEY если не задан
if [ -z "$WALLET_ENCRYPTION_KEY" ]; then
    WALLET_ENCRYPTION_KEY=$(python3 -c "import os; print(os.urandom(32).hex())")
    echo "✅ Сгенерирован WALLET_ENCRYPTION_KEY: $WALLET_ENCRYPTION_KEY"
    echo "   Сохрани его в надёжном месте! Без него нельзя расшифровать кошельки пользователей."
fi

# Записываем .env
cat > "$ENV_FILE" << EOF
# PolyScore Production Secrets
# Сгенерировано автоматически — НЕ КОММИТЬ В GIT

BOT_TOKEN=${BOT_TOKEN}
OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
POLY_API_KEY=${POLY_API_KEY}
POLY_SECRET=${POLY_SECRET}
POLY_PASSPHRASE=${POLY_PASSPHRASE}
POLY_PRIVATE_KEY=${POLY_PRIVATE_KEY}
WALLET_ENCRYPTION_KEY=${WALLET_ENCRYPTION_KEY}
BUILDER_CODE=polyscore
DB_PATH=polyscore.db
EOF

echo ""
echo "✅ Файл .env создан: $ENV_FILE"
echo ""

# Проверяем что критичные ключи заполнены
MISSING=""
[ -z "$POLY_API_KEY" ]     && MISSING="$MISSING\n  ❌ POLY_API_KEY"
[ -z "$POLY_SECRET" ]      && MISSING="$MISSING\n  ❌ POLY_SECRET"
[ -z "$POLY_PASSPHRASE" ]  && MISSING="$MISSING\n  ❌ POLY_PASSPHRASE"
[ -z "$POLY_PRIVATE_KEY" ] && MISSING="$MISSING\n  ❌ POLY_PRIVATE_KEY"

if [ -n "$MISSING" ]; then
    echo "⚠️  Незаполненные ключи (бот запустится в demo-режиме):$MISSING"
    echo ""
    echo "   Заполни их в файле setup_secrets.sh и запусти снова."
else
    echo "✅ Все production ключи заполнены!"
    echo "   Запускай бота: python fix_and_run.py"
fi
