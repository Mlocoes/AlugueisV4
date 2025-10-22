#!/bin/bash

# Script de inicialização automática do Sistema de Aluguéis
# Este script garante que o sistema inicie automaticamente e reinicie em caso de falhas

echo "🚀 Iniciando Sistema de Aluguéis V4..."

# Verificar se o Docker está instalado e funcionando
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não está instalado. Instale o Docker primeiro."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose não está instalado. Instale o Docker Compose primeiro."
    exit 1
fi

# Parar containers existentes (se houver)
echo "🛑 Parando containers existentes..."
docker-compose down

# Limpar containers órfãos
echo "🧹 Limpando containers órfãos..."
docker system prune -f

# Iniciar o sistema
echo "🏗️ Construindo e iniciando containers..."
docker-compose up -d --build

# Aguardar inicialização
echo "⏳ Aguardando inicialização do sistema..."
sleep 10

# Verificar se o sistema está funcionando
echo "🔍 Verificando status do sistema..."
if curl -s -f http://localhost:8000/ > /dev/null; then
    echo "✅ Sistema iniciado com sucesso!"
    echo "🌐 Acesse: http://localhost:8000"
    echo ""
    echo "📊 Status dos containers:"
    docker-compose ps
else
    echo "❌ Falha ao iniciar o sistema. Verificando logs..."
    docker-compose logs
    exit 1
fi

echo ""
echo "💡 Comandos úteis:"
echo "  - Ver logs: docker-compose logs -f"
echo "  - Parar: docker-compose down"
echo "  - Reiniciar: docker-compose restart"