#!/bin/bash

# Script de instalação do serviço de monitoramento automático
# do Sistema de Aluguéis V4

SERVICE_FILE="alugueis-monitor.service"
SERVICE_PATH="/etc/systemd/system/$SERVICE_FILE"
PROJECT_DIR="/home/mloco/Escritorio/AlugueisV4"

echo "🔧 Instalando serviço de monitoramento automático..."

# Verificar se está executando como root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Este script deve ser executado como root (sudo)"
   exit 1
fi

# Copiar arquivo de serviço
cp "$PROJECT_DIR/$SERVICE_FILE" "$SERVICE_PATH"

# Recarregar systemd
systemctl daemon-reload

# Habilitar e iniciar o serviço
systemctl enable "$SERVICE_FILE"
systemctl start "$SERVICE_FILE"

echo "✅ Serviço instalado com sucesso!"
echo ""
echo "📊 Status do serviço:"
systemctl status "$SERVICE_FILE" --no-pager -l

echo ""
echo "💡 Comandos úteis:"
echo "  - Ver status: sudo systemctl status $SERVICE_FILE"
echo "  - Ver logs: sudo journalctl -u $SERVICE_FILE -f"
echo "  - Parar: sudo systemctl stop $SERVICE_FILE"
echo "  - Reiniciar: sudo systemctl restart $SERVICE_FILE"