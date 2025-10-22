# 📤 Upload para GitHub - Guia Rápido

## 🚀 Como subir o projeto para GitHub

### Método 1: Script Automático (Recomendado)

```bash
# 1. Executar o script de upload
./upload_to_github.sh nome-do-seu-repositorio

# Exemplo:
./upload_to_github.sh sistema-alugueis-v4
```

O script irá:
- ✅ Inicializar git (se necessário)
- ✅ Criar .gitignore
- ✅ Fazer commit inicial
- ✅ Criar repositório no GitHub (se GitHub CLI estiver instalado)
- ✅ Fazer push do código

### Método 2: Passo a Passo Manual

```bash
# 1. Inicializar git
git init

# 2. Configurar usuário
git config user.name "Seu Nome"
git config user.email "seu-email@example.com"

# 3. Adicionar arquivos
git add .

# 4. Fazer commit
git commit -m "Initial commit - Sistema de Alugueis V4"

# 5. Criar repositório no GitHub (github.com/new)
# Nome sugerido: sistema-alugueis-v4

# 6. Conectar repositório local ao GitHub
git remote add origin https://github.com/SEU-USUARIO/NOME-REPOSITORIO.git

# 7. Enviar código
git push -u origin main
```

## 📋 Pré-requisitos

### GitHub CLI (Opcional, mas recomendado)
```bash
# Ubuntu/Debian
sudo apt install gh

# Login no GitHub
gh auth login
```

### Sem GitHub CLI
- Criar repositório manualmente em [github.com/new](https://github.com/new)
- Seguir os passos manuais acima

## 🔍 Arquivos Importantes

- `docker-compose.yml` - Para executar o sistema
- `requirements.txt` - Dependências Python
- `README.md` - Documentação completa
- `SEGURANCA.md` - Guia de segurança
- `REVISAO_SISTEMA.md` - Status do desenvolvimento

## ⚠️ Arquivos Excluídos (.gitignore)

O `.gitignore` automaticamente exclui:
- Banco de dados (`*.db`)
- Ambiente virtual (`venv/`)
- Arquivos de log (`*.log`)
- Arquivos temporários
- Configurações sensíveis (`.env`)

## 🎯 Próximos Passos

Após o upload:
1. ✅ Verificar se o código está no GitHub
2. ✅ Configurar GitHub Actions (se necessário)
3. ✅ Adicionar colaboradores
4. ✅ Criar issues para melhorias
5. ✅ Configurar branch protection

---

**💡 Dica**: Use o script automático para facilitar o processo!