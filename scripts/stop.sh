#!/bin/bash
# Para o bot
PID_FILE="$(dirname "$0")/../data/bot.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"
        echo "Bot parado (PID: $PID)"
    else
        echo "Bot não está rodando (PID $PID não existe)"
    fi
    rm -f "$PID_FILE"
else
    echo "Arquivo PID não encontrado"
fi
