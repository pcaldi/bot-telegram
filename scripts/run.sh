#!/bin/bash
# Inicia o bot em background com logs
cd "$(dirname "$0")/.."

echo "Iniciando bot-telegram-ofertas..."
echo "Logs: tail -f data/bot.log"
echo "Parar: kill \$(cat data/bot.pid)"

nohup python scripts/main.py >> data/bot.log 2>&1 &
echo $! > data/bot.pid
echo "Bot PID: $(cat data/bot.pid)"
