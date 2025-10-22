#!/bin/bash

# Script de Segurança - Verificação e Correção de Permissões
# Este script verifica e corrige permissões inseguras no sistema

echo "🔒 Verificando segurança do sistema..."

# Verificar se estamos rodando como root
if [[ $EUID -eq 0 ]]; then
    echo "❌ ALERTA: Este script não deve ser executado como root!"
    echo "Execute como usuário normal: $0"
    exit 1
fi

# Verificar permissões do banco de dados
DB_FILE="/home/mloco/Escritorio/AlugueisV4/alugueis.db"
if [[ -f "$DB_FILE" ]]; then
    DB_OWNER=$(stat -c '%U' "$DB_FILE")
    DB_PERMS=$(stat -c '%a' "$DB_FILE")

    if [[ "$DB_OWNER" == "root" ]]; then
        echo "❌ ALERTA: Banco de dados pertence ao root!"
        echo "Corrigindo permissões..."
        sudo chown mloco:mloco "$DB_FILE"
    fi

    if [[ "$DB_PERMS" -gt "644" ]]; then
        echo "❌ ALERTA: Permissões do banco muito permissivas ($DB_PERMS)"
        chmod 644 "$DB_FILE"
    fi
fi

# Verificar arquivos de configuração sensíveis
SENSITIVE_FILES=(
    "/home/mloco/Escritorio/AlugueisV4/app/core/config.py"
    "/home/mloco/Escritorio/AlugueisV4/.env"
    "/home/mloco/Escritorio/AlugueisV4/server.log"
)

for file in "${SENSITIVE_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        perms=$(stat -c '%a' "$file")
        if [[ "$perms" -gt "600" ]]; then
            echo "❌ ALERTA: Arquivo $file tem permissões muito permissivas ($perms)"
            chmod 600 "$file"
        fi
    fi
done

# Verificar processos rodando como root
ROOT_PROCESSES=$(ps aux | grep -E "(uvicorn|python.*app)" | grep root | grep -v grep)
if [[ -n "$ROOT_PROCESSES" ]]; then
    echo "❌ ALERTA: Processos rodando como root:"
    echo "$ROOT_PROCESSES"
    echo "Considere parar estes processos e reiniciar com usuário não-root"
fi

# Verificar contêiners Docker
DOCKER_CONTAINERS=$(docker ps --format "table {{.ID}}\t{{.Image}}\t{{.Names}}" | grep alugueis)
if [[ -n "$DOCKER_CONTAINERS" ]]; then
    echo "📋 Contêiners Docker ativos:"
    echo "$DOCKER_CONTAINERS"
    echo "Verifique se estão rodando como usuário não-root"
fi

echo "✅ Verificação de segurança concluída!"
echo ""
echo "📋 Recomendações de segurança:"
echo "1. Nunca execute a aplicação como root"
echo "2. Use usuários não-root em contêiners Docker"
echo "3. Mantenha permissões mínimas necessárias (600 para arquivos sensíveis)"
echo "4. Monitore processos e logs regularmente"
echo "5. Use HTTPS em produção"
echo "6. Implemente rate limiting e validação de entrada"