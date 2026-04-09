#!/bin/bash
# PolyScore — управление ботом
# Использование: bash polyscore.sh [start|stop|restart|status|logs]

PLIST_NAME="com.polyscore.bot"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"
LOG_DIR="$HOME/Library/Logs/polyscore"

case "$1" in
    start)
        launchctl load "$PLIST_PATH"
        echo "✅ PolyScore запущен"
        ;;
    stop)
        launchctl unload "$PLIST_PATH"
        echo "🛑 PolyScore остановлен"
        ;;
    restart)
        launchctl unload "$PLIST_PATH" 2>/dev/null || true
        sleep 1
        launchctl load "$PLIST_PATH"
        echo "🔄 PolyScore перезапущен"
        ;;
    status)
        if launchctl list | grep -q "$PLIST_NAME"; then
            PID=$(launchctl list | grep "$PLIST_NAME" | awk '{print $1}')
            echo "✅ PolyScore работает (PID: $PID)"
        else
            echo "🔴 PolyScore не запущен"
        fi
        ;;
    logs)
        tail -f "$LOG_DIR/polyscore.log"
        ;;
    errors)
        tail -50 "$LOG_DIR/polyscore_error.log"
        ;;
    *)
        echo "Использование: bash polyscore.sh [start|stop|restart|status|logs|errors]"
        ;;
esac
