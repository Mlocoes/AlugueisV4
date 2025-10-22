#!/bin/bash

# Script para subir o projeto AlugueisV4 para GitHub
# Uso: ./upload_to_github.sh <nome-do-repositorio>

set -e

# Verificar se foi passado o nome do repositório
if [ $# -eq 0 ]; then
    echo "Erro: Você deve fornecer o nome do repositório como parâmetro"
    echo "Uso: $0 <nome-do-repositorio>"
    echo "Exemplo: $0 sistema-alugueis-v4"
    exit 1
fi

REPO_NAME=$1
GITHUB_USER="Mlocoes"

echo "🚀 Iniciando upload do projeto AlugueisV4 para GitHub..."
echo "📁 Repositório: $REPO_NAME"
echo "👤 Usuário: $GITHUB_USER"
echo ""

# Verificar se git está instalado
if ! command -v git &> /dev/null; then
    echo "❌ Git não está instalado. Instale o git primeiro."
    exit 1
fi

# Verificar se gh (GitHub CLI) está instalado
if ! command -v gh &> /dev/null; then
    echo "⚠️  GitHub CLI não está instalado."
    echo "📝 Você pode instalá-lo com: sudo apt install gh"
    echo "🔗 Ou baixe de: https://cli.github.com/"
    echo ""
    echo "Continuando sem GitHub CLI..."
    USE_GH=false
else
    USE_GH=true
fi

# Inicializar repositório git se não existir
if [ ! -d ".git" ]; then
    echo "📝 Inicializando repositório git..."
    git init
    echo "✅ Repositório git inicializado"
else
    echo "✅ Repositório git já existe"
fi

# Configurar usuário git (se não estiver configurado)
if [ -z "$(git config user.name)" ]; then
    echo "📝 Configurando usuário git..."
    git config user.name "Mlocoes"
    git config user.email "mlocoes@example.com"
    echo "✅ Usuário git configurado"
fi

# Adicionar .gitignore se não existir
if [ ! -f ".gitignore" ]; then
    echo "📝 Criando .gitignore..."
    cat > .gitignore << 'EOF'
# Arquivos de banco de dados
*.db
*.sqlite
*.sqlite3

# Ambiente virtual Python
venv/
env/
ENV/
.venv/

# Arquivos de log
*.log
server.log
monitor.log

# Arquivos temporários
*.tmp
*.temp
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Arquivos de configuração sensíveis
.env
.env.local
.env.production

# Arquivos do sistema
.DS_Store
Thumbs.db

# Arquivos de backup
*.bak
*.backup
*~

# Arquivos de IDE
.vscode/
.idea/
*.swp
*.swo

# Arquivos de teste temporários
test_*.py
debug_*.html
teste_*.xlsx
EOF
    echo "✅ .gitignore criado"
fi

# Adicionar todos os arquivos
echo "📝 Adicionando arquivos ao git..."
git add .

# Fazer commit inicial
echo "📝 Fazendo commit inicial..."
git commit -m "Initial commit - Sistema de Alugueis V4

- Sistema completo de gestão de aluguéis
- Backend FastAPI com autenticação JWT
- Frontend com JavaScript vanilla
- Banco de dados SQLite
- Docker containerizado
- Funcionalidades: Imóveis, Proprietários, Participações, Aluguéis"

echo "✅ Commit realizado"

# Criar repositório no GitHub
if [ "$USE_GH" = true ]; then
    echo "📝 Criando repositório no GitHub..."
    if gh repo create "$REPO_NAME" --public --source=. --remote=origin --push; then
        echo "✅ Repositório criado e código enviado para GitHub!"
        echo "🔗 URL: https://github.com/$GITHUB_USER/$REPO_NAME"
    else
        echo "❌ Erro ao criar repositório com GitHub CLI"
        echo "📝 Você pode criar manualmente em: https://github.com/new"
        echo "📝 Depois execute:"
        echo "   git remote add origin https://github.com/$GITHUB_USER/$REPO_NAME.git"
        echo "   git push -u origin main"
    fi
else
    echo "📝 GitHub CLI não encontrado. Crie o repositório manualmente:"
    echo "   1. Acesse: https://github.com/new"
    echo "   2. Nome do repositório: $REPO_NAME"
    echo "   3. Deixe público"
    echo "   4. Não inicialize com README, .gitignore ou license"
    echo ""
    echo "📝 Depois execute estes comandos:"
    echo "   git remote add origin https://github.com/$GITHUB_USER/$REPO_NAME.git"
    echo "   git push -u origin main"
    echo ""
    echo "🔗 URL do repositório será: https://github.com/$GITHUB_USER/$REPO_NAME"
fi

echo ""
echo "🎉 Processo concluído!"
echo "📚 Documentação importante:"
echo "   - README.md contém instruções de instalação"
echo "   - docker-compose.yml para executar o sistema"
echo "   - requirements.txt para dependências Python"