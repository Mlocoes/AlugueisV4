#!/bin/bash

# Script de monitoramento do Sistema de Aluguéis
# Verifica se o sistema está funcionando e reinicia se necessário

URL="http://localhost:8000"
LOG_FILE="/home/mloco/Escritorio/AlugueisV4/monitor.log"
PROJECT_DIR="/home/mloco/Escritorio/AlugueisV4"

# Função para log
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
    echo "$1"
}

# Verificar se o sistema está respondendo
check_system() {
    if curl -s -f --max-time 10 "$URL" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Reiniciar o sistema
restart_system() {
    log "🔄 Reiniciando sistema..."
    cd "$PROJECT_DIR" || exit 1

    # Parar containers
    docker-compose down

    # Limpar e reiniciar
    docker system prune -f
    docker-compose up -d --build

    # Aguardar inicialização
    sleep 15

    # Verificar se reiniciou com sucesso
    if check_system; then
        log "✅ Sistema reiniciado com sucesso"
    else
        log "❌ Falha ao reiniciar sistema"
        # Tentar novamente em 5 minutos
        sleep 300
        if check_system; then
            log "✅ Sistema reiniciado na segunda tentativa"
        else
            log "❌ Sistema continua com falha após segunda tentativa"
        fi
    fi
}

# Verificação principal
log "🔍 Verificando status do sistema..."

if check_system; then
    log "✅ Sistema funcionando normalmente"
else
    log "❌ Sistema não está respondendo"
    restart_system
fi