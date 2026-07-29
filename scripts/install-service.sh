#!/bin/bash
# Instala o bot como serviço systemd (inicia automaticamente com o PC)
set -e

SERVICE_NAME="bot-telegram-ofertas"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "Instalando serviço systemd..."

# Copia o arquivo de serviço
sudo cp "${SCRIPT_DIR}/bot-telegram-ofertas.service" "$SERVICE_FILE"

# Recarrega systemd
sudo systemctl daemon-reload

# Habilita e inicia o serviço
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl start "$SERVICE_NAME"

echo ""
echo "Serviço instalado e iniciado!"
echo ""
echo "Comandos úteis:"
echo "  sudo systemctl status $SERVICE_NAME   # Ver status"
echo "  sudo systemctl restart $SERVICE_NAME   # Reiniciar"
echo "  sudo systemctl stop $SERVICE_NAME      # Parar"
echo "  journalctl -u $SERVICE_NAME -f         # Ver logs em tempo real"
