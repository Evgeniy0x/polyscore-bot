#!/bin/bash
# PolyScore Bot Runner — перезапуск при падении
# Использование: bash run_bot.sh

cd "$(dirname "$0")"
LOGFILE="$(pwd)/bot.log"
PIDFILE="$(pwd)/bot.pid"

# Проверяем, не запущен ли уже
if [ -f "$PIDFILE" ]; then
    OLD_PID=$(cat "$PIDFILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "✅ Бот уже работает, PID: $OLD_PID"
        exit 0
    fi
    rm -f "$PIDFILE"
fi

echo "🚀 Запускаю PolyScore бота..."
echo "   Логи: $LOGFILE"

# Запускаем с перезапуском при падении
while true; do
    echo "[$(date)] Запуск бота..." >> "$LOGFILE"
    python3 bot.py >> "$LOGFILE" 2>&1 &
    BOT_PID=$!
    echo "$BOT_PID" > "$PIDFILE"
    echo "   PID: $BOT_PID"

    # Ждём завершения процесса
    wait $BOT_PID
    EXIT_CODE=$?

    echo "[$(date)] Бот упал с кодом $EXIT_CODE. Перезапуск через 3 сек..." >> "$LOGFILE"
    rm -f "$PIDFILE"
    sleep 3
done
