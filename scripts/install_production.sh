#!/bin/bash

# Script de instalação completa para PRODUÇÃO
# Sistema de Aluguéis V4 - Configuração de Produção

set -e  # Para o script em caso de erro

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "🏭 INSTALAÇÃO DE PRODUÇÃO - SISTEMA DE ALUGUÉIS V4"
echo "=================================================="

# Verificar se estamos no diretório correto
if [ ! -f "app/main.py" ]; then
    echo "❌ Erro: Execute este script do diretório raiz do projeto AlugueisV4"
    exit 1
fi

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Erro: Docker não encontrado. Instale o Docker primeiro."
    echo "   Ubuntu/Debian: sudo apt install docker.io docker-compose"
    echo "   CentOS/RHEL: sudo yum install docker docker-compose"
    exit 1
fi

# Verificar se Docker Compose está instalado
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Erro: Docker Compose não encontrado. Instale o Docker Compose primeiro."
    exit 1
fi

echo "🐳 Docker e Docker Compose detectados"

# Verificar se .env existe
if [ ! -f ".env" ]; then
    echo "⚠️  Arquivo .env não encontrado. Copiando .env.example..."
    cp .env.example .env
    echo "✅ Arquivo .env criado. Edite-o com suas configurações de produção!"
    echo ""
    echo "IMPORTANTE: Configure as seguintes variáveis no .env:"
    echo "  - DATABASE_URL: URL do PostgreSQL de produção"
    echo "  - SECRET_KEY: Chave secreta forte para produção"
    echo "  - ALLOWED_ORIGINS: Domínios permitidos"
    echo ""
    read -p "Pressione ENTER após configurar o .env..."
fi

echo ""
echo "🔧 CONFIGURANDO AMBIENTE DE PRODUÇÃO"
echo "-------------------------------------"

# Parar containers existentes
echo "  🛑 Parando containers existentes..."
docker-compose down || true

# Limpar imagens não utilizadas (opcional)
read -p "Deseja limpar imagens Docker não utilizadas? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "  🧹 Limpando imagens não utilizadas..."
    docker system prune -f
fi

echo ""
echo "🏗️  CONSTRUINDO E INICIANDO SERVIÇOS"
echo "-------------------------------------"

# Construir e iniciar serviços
echo "  📦 Construindo imagens..."
docker-compose build --no-cache

echo "  🚀 Iniciando serviços..."
docker-compose up -d

echo "  ⏳ Aguardando serviços ficarem prontos..."
sleep 30

# Verificar se os serviços estão rodando
echo "  🔍 Verificando status dos serviços..."
if docker-compose ps | grep -q "Up"; then
    echo "  ✅ Serviços iniciados com sucesso!"
else
    echo "  ❌ Erro ao iniciar serviços. Verifique os logs:"
    docker-compose logs
    exit 1
fi

echo ""
echo "🗄️  CONFIGURANDO BANCO DE DADOS"
echo "-------------------------------"

# Executar migrações dentro do container
echo "  📋 Executando migrações do banco..."
if docker-compose exec -T app alembic upgrade head; then
    echo "  ✅ Migrações executadas com sucesso!"
else
    echo "  ❌ Erro nas migrações. Verifique os logs do banco:"
    docker-compose logs db
    exit 1
fi

echo ""
echo "👤 CRIANDO USUÁRIO ADMINISTRADOR"
echo "---------------------------------"

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

# Executar script dentro do container
if docker-compose exec -T app python3 scripts/create_admin_interactive.py --nome "$ADMIN_NOME" --email "$ADMIN_EMAIL" --password "$ADMIN_PASSWORD"; then
    echo ""
    echo "🎉 INSTALAÇÃO DE PRODUÇÃO CONCLUÍDA!"
    echo "===================================="
    echo "✅ Serviços Docker configurados"
    echo "✅ Banco de dados PostgreSQL pronto"
    echo "✅ Migrações executadas"
    echo "✅ Usuário administrador criado"
    echo ""
    echo "🌐 Acesse a aplicação:"
    echo "   - URL: Configure seu domínio/reverse proxy"
    echo "   - Porta interna: 8000"
    echo "   - Login: Use o email e senha configurados"
    echo ""
    echo "🛠️  Comandos úteis:"
    echo "   - Ver logs: docker-compose logs -f"
    echo "   - Parar: docker-compose down"
    echo "   - Reiniciar: docker-compose restart"
    echo ""
    echo "🔒 CONFIGURAÇÕES DE SEGURANÇA:"
    echo "   - Configure HTTPS no reverse proxy"
    echo "   - Mude a SECRET_KEY no .env"
    echo "   - Configure ALLOWED_ORIGINS adequadamente"
    echo "   - Considere usar secrets do Docker"
else
    echo "❌ Erro ao criar usuário administrador!"
    echo "   Verifique os logs: docker-compose logs app"
    exit 1
fi
