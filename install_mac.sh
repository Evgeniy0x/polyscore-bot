#!/bin/bash
# PolyScore — Установщик для Mac mini
# Запусти ОДИН РАЗ: bash install_mac.sh
# После этого бот запускается автоматически при каждом старте системы

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLIST_NAME="com.polyscore.bot"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"
LOG_DIR="$HOME/Library/Logs/polyscore"
PYTHON=$(which python3)

echo "╔══════════════════════════════════════╗"
echo "║      PolyScore — Установка           ║"
echo "╚══════════════════════════════════════╝"
echo ""
echo "📁 Папка проекта: $SCRIPT_DIR"
echo "🐍 Python: $PYTHON"
echo ""

# ── 1. Установка зависимостей ─────────────────────────────────────────────────
echo "📦 Устанавливаю зависимости..."
$PYTHON -m pip install -r "$SCRIPT_DIR/requirements.txt" --quiet
echo "✅ Зависимости установлены"
echo ""

# ── 2. Создать папку для логов ────────────────────────────────────────────────
mkdir -p "$LOG_DIR"
echo "📋 Папка логов: $LOG_DIR"

# ── 3. Удалить старый plist если есть ────────────────────────────────────────
if [ -f "$PLIST_PATH" ]; then
    echo "🗑️  Удаляю старую версию..."
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
    rm "$PLIST_PATH"
fi

# ── 4. Создать plist ──────────────────────────────────────────────────────────
cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$PLIST_NAME</string>

    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON</string>
        <string>$SCRIPT_DIR/bot.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>$SCRIPT_DIR</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>DB_PATH</key>
        <string>$HOME/Library/Application Support/polyscore/polyscore.db</string>
        <key>BUILDER_CODE</key>
        <string>polyscore</string>
    </dict>

    <!-- Автозапуск при входе в систему -->
    <key>RunAtLoad</key>
    <true/>

    <!-- Перезапускать при падении -->
    <key>KeepAlive</key>
    <true/>

    <!-- Логи -->
    <key>StandardOutPath</key>
    <string>$LOG_DIR/polyscore.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/polyscore_error.log</string>

    <!-- Ждать 5 секунд перед перезапуском -->
    <key>ThrottleInterval</key>
    <integer>5</integer>
</dict>
</plist>
EOF

echo "✅ plist создан: $PLIST_PATH"

# ── 5. Создать папку для БД ───────────────────────────────────────────────────
mkdir -p "$HOME/Library/Application Support/polyscore"

# ── 6. Загрузить и запустить ──────────────────────────────────────────────────
echo ""
echo "🚀 Запускаю бота..."
launchctl load "$PLIST_PATH"
sleep 2

# Проверка
if launchctl list | grep -q "$PLIST_NAME"; then
    echo ""
    echo "╔══════════════════════════════════════╗"
    echo "║   ✅ PolyScore запущен и работает!   ║"
    echo "╚══════════════════════════════════════╝"
    echo ""
    echo "📋 Логи: tail -f $LOG_DIR/polyscore.log"
    echo "🛑 Остановить: launchctl unload $PLIST_PATH"
    echo "▶️  Запустить: launchctl load $PLIST_PATH"
    echo ""
else
    echo ""
    echo "⚠️  Бот запустился, проверь логи:"
    echo "cat $LOG_DIR/polyscore_error.log"
fi
