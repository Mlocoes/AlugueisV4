#!/bin/bash

# Script de instalação completa do Sistema de Aluguéis
# Cria base de dados, executa migrações e configura primeiro usuário administrador

set -e  # Para o script em caso de erro

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "🏠 INSTALAÇÃO COMPLETA - SISTEMA DE ALUGUÉIS V4"
echo "================================================"

# Verificar se estamos no diretório correto
if [ ! -f "app/main.py" ]; then
    echo "❌ Erro: Execute este script do diretório raiz do projeto AlugueisV4"
    exit 1
fi

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Erro: Python 3 não encontrado. Instale o Python 3 primeiro."
    exit 1
fi

# Verificar se pip está instalado
if ! command -v pip3 &> /dev/null; then
    echo "❌ Erro: pip3 não encontrado. Instale o pip3 primeiro."
    exit 1
fi

echo "📦 Verificando dependências..."
if [ ! -d "venv" ]; then
    echo "  Criando ambiente virtual..."
    python3 -m venv venv
fi

echo "  Ativando ambiente virtual..."
source venv/bin/activate

echo "  Instalando dependências..."
pip install -r requirements.txt

echo ""
echo "🗄️  CONFIGURAÇÃO DA BASE DE DADOS"
echo "---------------------------------"

# Perguntar se quer criar BD do zero
read -p "Deseja criar a base de dados do zero? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "  🗑️  Removendo base de dados existente..."
    rm -f test.db

    echo "  📋 Executando migrações..."
    if [ -f ".env" ]; then
        export $(grep -v '^#' .env | xargs)
    fi
    # Forçar SQLite para desenvolvimento local
    export DATABASE_URL="sqlite:///test.db"
    export PYTHONPATH="$PWD"
    alembic upgrade head

    echo "  ✅ Base de dados criada com sucesso!"
else
    echo "  ⏭️  Pulando criação da base de dados."
    if [ ! -f "test.db" ]; then
        echo "  ⚠️  Base de dados não existe. Executando migrações..."
        if [ -f ".env" ]; then
            export $(grep -v '^#' .env | xargs)
        fi
        export DATABASE_URL="sqlite:///test.db"
        export PYTHONPATH="$PWD"
        alembic upgrade head
    fi
fi

echo ""
echo "👤 CRIAÇÃO DO PRIMEIRO USUÁRIO ADMINISTRADOR"
echo "---------------------------------------------"

echo "Sugestão: admin / admin00"
echo ""

# Pedir dados do administrador
read -p "Nome do administrador: " ADMIN_NOME
read -p "Email do administrador: " ADMIN_EMAIL
read -s -p "Senha do administrador: " ADMIN_PASSWORD
echo
read -s -p "Confirme a senha: " ADMIN_PASSWORD_CONFIRM
echo

# Verificar se senhas coincidem
if [ "$ADMIN_PASSWORD" != "$ADMIN_PASSWORD_CONFIRM" ]; then
    echo "❌ Erro: Senhas não coincidem!"
    exit 1
fi

# Verificar se campos estão preenchidos
if [ -z "$ADMIN_NOME" ] || [ -z "$ADMIN_EMAIL" ] || [ -z "$ADMIN_PASSWORD" ]; then
    echo "❌ Erro: Todos os campos são obrigatórios!"
    exit 1
fi

echo "  👤 Criando usuário administrador..."

# Executar script Python para criar o usuário
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi
export DATABASE_URL="sqlite:///test.db"
export PYTHONPATH="$PWD"
if python3 scripts/create_admin_interactive.py --nome "$ADMIN_NOME" --email "$ADMIN_EMAIL" --password "$ADMIN_PASSWORD"; then
    echo ""
    echo "🎉 INSTALAÇÃO CONCLUÍDA COM SUCESSO!"
    echo "===================================="
    echo "✅ Base de dados configurada"
    echo "✅ Usuário administrador criado"
    echo ""
    echo "🚀 Para iniciar o sistema:"
    echo "   ./start.sh"
    echo ""
    echo "🌐 Acesse: http://localhost:8000"
    echo "👤 Login: Use o email e senha configurados"
else
    echo "❌ Erro ao criar usuário administrador!"
    exit 1
fi