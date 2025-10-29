# 🏠 Sistema de Gestão de Aluguéis - AlugueisV4

Sistema completo para gestão de imóveis, aluguéis e proprietários com controle financeiro e relatórios.

**Status**: 🟡 Em Desenvolvimento (60% completo)  
**Versão**: 1.0.0-alpha  
**Última Atualização**: 20 de Outubro de 2025

> ⚠️ **AVISO**: Sistema funcional mas **NÃO pronto para produção**. Faltam validações críticas de negócio e controle de acesso completo. Veja `REVISAO_SISTEMA.md` para detalhes.

## 🔒 Segurança

> 🚨 **IMPORTANTE**: Este sistema foi corrigido para **NÃO executar como root**. Problemas de segurança críticos foram identificados e resolvidos.

### ✅ Correções de Segurança Implementadas
- **Usuário não-root**: Dockerfile e Docker Compose atualizados para usar `appuser`
- **Permissões seguras**: Arquivos sensíveis com permissões 600
- **Script de verificação**: `security_check.sh` para monitoramento contínuo
- **Documentação**: Guia completo em `SEGURANCA.md`

### 🛡️ Verificação de Segurança
```bash
# Executar verificação automática
./security_check.sh

# Ou diretamente
scripts/security_check.sh
```

**Nunca execute este sistema como root!** Use sempre usuários não-privilegiados.

## 📋 Sobre o Projeto

**AlugueisV4** implementa **60% das funcionalidades** especificadas em `PROMPT.md`, com backend **FastAPI** e frontend moderno usando **TailwindCSS**, **Handsontable** e **Chart.js**.

## ✨ Funcionalidades Implementadas

### ✅ Core (100%)
- **Autenticação JWT**: Login seguro com tokens
- **CRUD Completo**: Criar, ler, atualizar e excluir todas entidades
- **API RESTful**: 9 routers organizados e documentados
- **Banco de Dados**: SQLAlchemy com SQLite (migração para PostgreSQL planejada)

### ✅ Gestão (100%)
- **Usuários/Proprietários**: Cadastro com geração automática de username
- **Imóveis**: Controle de propriedades (nome, endereço, status)
- **Participações**: Sistema de co-propriedade com percentuais
- **Aluguéis**: Registro de valores, taxas e DARF
- **Alias**: Grupos de proprietários para relatórios consolidados
- **Transferências**: Movimentações financeiras entre contas
- **Permissões**: Estrutura para controle de acesso (lógica parcial)

### ✅ Interface (80%)
- **Dashboard**: Gráficos com Chart.js e estatísticas gerais
- **9 Páginas HTML**: Login, Dashboard, CRUD de todas entidades
- **Design Moderno**: TailwindCSS responsivo
- **Tabelas Interativas**: Handsontable (modo leitura, edição inline planejada)

### ⚠️ Parcialmente Implementado (30-50%)
- **Controle de Acesso**: Estrutura existe, lógica não aplicada

### Permissões financeiras (visualizar vs editar)

- O sistema tem um modelo granular de permissões financeiras (`permissoes_financeiras`) que relaciona usuários a proprietários com duas flags:
   - `visualizar` — permite ver (leitura) os dados financeiros do proprietário;
   - `editar` — permite criar/alterar/excluir dados financeiros do proprietário.

- Com a correção recente, endpoints de leitura (relatórios, listagens, detalhes) respeitam a flag `visualizar` enquanto operações mutativas (POST/PUT/DELETE) exigem `editar`.

- Observações de rollout:
   - Administradores (`tipo == 'administrador'`) têm acesso total por padrão.
   - Relatórios e dashboard aplicam filtros a nível de banco (WHERE id_proprietario IN (...)) para evitar exposição acidental de dados e para melhor desempenho.
   - Frontend tenta ocultar controles de edição quando o usuário não tem a flag `editar`; ainda assim o backend valida permissões em todos endpoints (sempre confie no backend para segurança).

Consulte `app/core/permissions.py` para comportamento e os routers em `app/routes/` para exemplos de aplicação.

- **Validações de Negócio**: Básicas apenas (falta soma participações = 100%)
- **Relatórios**: Template existe, filtros não funcionam completamente
- **Filtros Avançados**: Estrutura básica, funcionalidade limitada

### ❌ Não Implementado (0%)
- **Importação Excel**: Planejado mas não iniciado
- **Exportação Relatórios**: PDF/Excel não implementado
- **Testes Automatizados**: pytest não configurado
- **PostgreSQL**: Usando SQLite (migração planejada)
- **Cálculos Automáticos**: Taxa por proprietário, totais anuais
- **Responsividade Mobile**: Parcial, precisa melhorias

## 🛠️ Tecnologias

### Backend
- **FastAPI**: Framework web moderno e rápido
- **SQLAlchemy 2.0**: ORM para banco de dados
- **SQLite/PostgreSQL**: Banco de dados
- **Pydantic**: Validação de dados
- **JWT**: Autenticação segura

### Frontend (Planejado)
- **HTML5/CSS3**: ✅ Implementado
- **TailwindCSS**: ✅ Implementado
- **Handsontable**: ✅ Implementado (modo leitura)
- **Chart.js**: ✅ Implementado (dashboard)

### DevOps
- **Docker**: Containerização
- **Docker Compose**: Orquestração de serviços

## 📁 Estrutura do Projeto

```
AlugueisV4/
├── app/
│   ├── core/           # Configurações e utilitários
│   │   ├── auth.py     # Autenticação JWT
│   │   ├── config.py   # Configurações da aplicação
│   │   └── database.py # Conexão com banco
│   ├── models/         # Modelos SQLAlchemy
│   ├── routes/         # Endpoints da API
│   ├── schemas/        # Schemas Pydantic
│   ├── static/         # Arquivos estáticos
│   ├── templates/      # Templates HTML
│   └── main.py         # Aplicação principal
├── scripts/            # Scripts de utilidade e manutenção
├── test_scripts/       # Scripts de teste e configuração
├── tests/              # Testes automatizados
├── alembic/            # Migrações de banco
├── excel/              # Modelos Excel para importação
├── requirements.txt    # Dependências Python
├── Dockerfile          # Container da aplicação
├── docker-compose.yml  # Orquestração
└── README.md           # Documentação
```

## �️ Scripts Disponíveis

O projeto inclui vários scripts organizados em diretórios específicos:

### Scripts de Utilidade (`scripts/`)
- `scripts/start.sh` - Inicialização rápida do sistema
- `scripts/monitor.sh` - Monitoramento automático de saúde
- `scripts/install-service.sh` - Instalação do serviço SystemD
- `scripts/security_check.sh` - Verificação de segurança
- `scripts/migrate.sh` - Migração para PostgreSQL
- `scripts/create_admin_user.py` - Criar usuário administrador
- `scripts/create_admin_postgres.py` - Configurar admin no PostgreSQL
- `scripts/dashboard_verification.py` - Verificar dashboard
- `scripts/test_final.py` - Testes finais do sistema

### Scripts de Teste (`test_scripts/`)
- `test_scripts/create_test_users.py` - Criar usuários de teste
- `test_scripts/setup_test_user.py` - Configurar usuário de teste
- `test_scripts/clear_all_rentals.py` - Limpar aluguéis de teste
- `test_scripts/clear_incorrect_data.py` - Limpar dados incorretos

> 💡 **Compatibilidade**: Scripts podem ser executados da raiz do projeto (shims automáticos) ou diretamente dos diretórios `scripts/` e `test_scripts/`.

## �🚀 Como Executar

### Desenvolvimento Local (Recomendado)

1. **Clone o repositório**:
   ```bash
   cd AlugueisV4
   ```

2. **Crie ambiente virtual e instale dependências**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ou venv\Scripts\activate no Windows
   pip install -r requirements.txt
   ```

3. **Execute as migrações** (primeira vez):
   ```bash
   alembic upgrade head
   ```

4. **Inicie o servidor**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Acesse a aplicação**:
   - Frontend: http://localhost:8000
   - Login: `admin` / `123` (auto-login habilitado em desenvolvimento)
   - API Docs: http://localhost:8000/docs

### Com Docker

1. **Execute com Docker Compose**:
   ```bash
   docker-compose up --build
   ```

2. **Acesse**:
   - http://localhost:8000

## 🔄 Inicialização Automática

O sistema agora conta com **reinicialização automática** para garantir alta disponibilidade.

### 🚀 Inicialização Rápida

```bash
# Script automático (recomendado)
./start.sh

# Ou diretamente do diretório scripts/
scripts/start.sh
```

### 📊 Monitoramento Automático

#### Opção 1: Serviço SystemD (Linux)
```bash
# Instalar serviço de monitoramento
sudo ./install-service.sh

# Ou diretamente
sudo scripts/install-service.sh

# Verificar status
sudo systemctl status alugueis-monitor.service

# Ver logs
sudo journalctl -u alugueis-monitor.service -f
```

#### Opção 2: Cron Job
```bash
# Adicionar ao crontab (verificar a cada 5 minutos)
*/5 * * * * /home/mloco/Escritorio/AlugueisV4/scripts/monitor.sh
```

#### Opção 3: Manual
```bash
# Verificar status manualmente
./monitor.sh

# Ou diretamente
scripts/monitor.sh

# Ver logs
tail -f monitor.log
```

### ⚙️ Configuração

- **Docker Compose**: Reinicialização automática configurada (`restart: unless-stopped`)
- **Monitoramento**: Verifica saúde a cada 60 segundos
- **Logs**: Arquivo `monitor.log` com histórico completo
- **Recuperação**: Tentativas automáticas de reinicialização em caso de falha

### 🛠️ Comandos Úteis

```bash
# Status dos containers
docker-compose ps

# Logs em tempo real
docker-compose logs -f

# Reiniciar manualmente
docker-compose restart

# Parar tudo
docker-compose down
```

## 📊 API Endpoints

### Autenticação
- `POST /auth/login` - Login com username/password (retorna JWT)
- `GET /auth/me` - Dados do usuário autenticado

### Usuários/Proprietários (`/api/usuarios`)
- `GET /api/usuarios/` - Listar todos
- `POST /api/usuarios/` - Criar (gera username automático)
- `GET /api/usuarios/{id}` - Buscar por ID
- `PUT /api/usuarios/{id}` - Atualizar
- `DELETE /api/usuarios/{id}` - Deletar

### Imóveis (`/api/imoveis`)
- `GET /api/imoveis/` - Listar todos
- `POST /api/imoveis/` - Criar novo
- `GET /api/imoveis/{id}` - Buscar por ID
- `PUT /api/imoveis/{id}` - Atualizar
- `DELETE /api/imoveis/{id}` - Deletar

### Participações (`/api/participacoes`)
- `GET /api/participacoes/` - Listar todas
- `POST /api/participacoes/` - Criar nova (% de propriedade)
- `GET /api/participacoes/{id}` - Buscar por ID
- `PUT /api/participacoes/{id}` - Atualizar
- `DELETE /api/participacoes/{id}` - Deletar

### Aluguéis (`/api/alugueis`)
- `GET /api/alugueis/` - Listar todos
- `POST /api/alugueis/` - Criar novo registro
- `GET /api/alugueis/{id}` - Buscar por ID  
- `PUT /api/alugueis/{id}` - Atualizar
- `DELETE /api/alugueis/{id}` - Deletar

### Alias (`/api/alias`)
- CRUD completo para grupos de proprietários

### Transferências (`/api/transferencias`)
- CRUD completo para movimentações financeiras

### Permissões (`/api/permissoes-financeiras`)
- CRUD completo para controle de acesso

### Dashboard (`/api/dashboard`)
- `GET /api/dashboard/stats` - Estatísticas gerais
- `GET /api/dashboard/receita` - Dados de receita mensal
- `GET /api/dashboard/proprietarios` - Dados por proprietário

> 📖 **Documentação Interativa**: Acesse http://localhost:8000/docs para testar todos os endpoints
- `GET /alugueis/` - Listar aluguéis
- `POST /alugueis/` - Criar aluguel

### Grupos (Alias)
- `GET /alias/` - Listar grupos
- `POST /alias/` - Criar grupo

### Transferências
- `GET /transferencias/` - Listar transferências
- `POST /transferencias/` - Criar transferência

### Permissões Financeiras
- `GET /permissoes-financeiras/` - Listar permissões
- `POST /permissoes-financeiras/` - Criar permissão

### Dashboard
- `GET /dashboard/` - Dados do dashboard

## 🗄️ Modelos de Dados

### Usuario
```python
id: int (PK)
username: str (único, gerado automaticamente do email)
nome: str
tipo: str  # 'administrador' ou 'usuario'
email: str (único)
telefone: str (opcional)
hashed_password: str
ativo: bool
```

### Imovel
```python
id: int (PK)
nome: str
endereco: str
alugado: bool
ativo: bool
```

### Participacao
```python
id: int (PK)
id_imovel: int (FK → imoveis.id)
id_proprietario: int (FK → usuarios.id)
participacao: Decimal  # 0 a 100 (percentual)
data_cadastro: Date
```

### Aluguel
```python
id: int (PK)
id_imovel: int (FK → imoveis.id)
id_proprietario: int (FK → usuarios.id)
aluguel_liquido: Decimal
taxa_administracao_total: Decimal
darf: Decimal
data_cadastro: Date
```

### Alias (Grupos)
```python
id: int (PK)
nome: str
ativo: bool
# Relação N:N com proprietários via alias_proprietarios
```

### Transferencia
```python
id: int (PK)
id_alias: int (FK → alias.id)
id_proprietario: int (FK → usuarios.id)
valor: Decimal
data_inicio: Date
data_fim: Date (opcional)
```

### PermissaoFinanceira
```python
id: int (PK)
id_usuario: int (FK → usuarios.id)
id_proprietario: int (FK → usuarios.id)
visualizar: bool
editar: bool
data_criacao: DateTime
```

## 🔐 Autenticação

O sistema utiliza **JWT (JSON Web Tokens)** para autenticação:

1. **Login**: `POST /auth/login` com username e password
2. **Token**: Receba o `access_token` na resposta
3. **Requisições**: Inclua o token no header:
   ```
   Authorization: Bearer <seu-token-aqui>
   ```

**Desenvolvimento**: Usuários de teste criados localmente (ver `CREDENCIAIS_TESTE.md`) — por padrão use `admin` / `admin00` e `user` / `123456`.

### Autenticação (estado atual)

O sistema usa tokens JWT. O frontend ARMAZENA O TOKEN EXCLUSIVAMENTE EM `sessionStorage` (comportamento desejado):

- Após login (`POST /api/auth/login/json`) o `access_token` é guardado no `sessionStorage` e enviado no header `Authorization: Bearer <token>` nas requisições.
- Navegação normal entre páginas NÃO limpa a sessão.
- Qualquer recarga completa da página (F5) limpa o `sessionStorage` e exige novo login — isto é intencional e corresponde ao requisito funcional do projeto.

CSRF e segurança:

- Para chamadas mutativas (POST/PUT/DELETE) o frontend envia um token CSRF gerado no cliente (armazenado em `sessionStorage`) como header `X-CSRF-Token`. O backend valida esse token quando aplicável (padrão double-submit).

Recomendações de produção:

- Em produção use HTTPS e valide tokens no backend; considere um fluxo com cookies HttpOnly e refresh tokens se desejar persistência entre reloads (opção não adotada por este requisito).
- Não confie no frontend para controle de acesso — o backend sempre valida permissões e tokens.

Como testar localmente:

1. Inicie a aplicação e abra `http://localhost:8000/login`.
2. Faça login com `admin` / `admin00`.
3. Navegue por várias páginas — a sessão permanece.
4. Pressione F5 em qualquer página — a sessão local é limpa e você será redirecionado para `/login`.

Notas:

- A implementação atual foi projetada para garantir que reloads do navegador não mantenham credenciais locais. Se você desejar uma estratégia diferente (tokens em cookies HttpOnly com refresh), eu posso ajudar a planejar e implementar essa mudança.

## 📈 Regras de Negócio

### ✅ Implementadas
- Validação de dados com Pydantic
- Relacionamentos entre entidades
- Autenticação obrigatória em todas as rotas

### ⚠️ Parcialmente Implementadas
- Geração automática de username a partir do email
- Validação básica de campos obrigatórios

### ❌ Não Implementadas (TODO)
- **Soma de Participações**: Validar que soma = 100% ± 0.4%
- **Cálculo Automático**: `taxa_admin_proprietario = taxa_admin_total * (participacao / 100)`
- **Aluguel Anual**: Soma automática por ano
- **Permissões Granulares**: Filtrar dados baseado em permissoes_financeiras
- **Histórico**: Versões de participações por data_cadastro

## 🧪 Testes

### Testes Manuais Disponíveis
```bash
# Scripts organizados em test_scripts/
test_scripts/create_test_users.py
test_scripts/setup_test_user.py
test_scripts/clear_all_rentals.py
test_scripts/clear_incorrect_data.py

# Ou da raiz (shims)
./create_test_users.py
./setup_test_user.py
./clear_all_rentals.py
./clear_incorrect_data.py
```

### Teste Interativo (API Docs)
Acesse http://localhost:8000/docs para testar todos os endpoints interativamente.

### Testes Automatizados (TODO)
```bash
pytest tests/  # Ainda não implementado
```

## 🛣️ Roadmap

### 📍 Versão Atual: 1.0.0-alpha (60% completo)

### 🎯 Próximas Versões

**v1.1** - Validações e Controle (2-3 semanas)
- Validação soma participações = 100%
- Controle de acesso completo
- Cálculos automáticos

**v1.2** - Frontend Avançado (2-3 semanas)
- Handsontable editável
- Filtros avançados
- Gráficos dinâmicos

**v1.3** - Import/Export (2 semanas)
- Importação Excel
- Exportação PDF/Excel

**v2.0** - Produção (1-2 meses)
- PostgreSQL
- Testes automatizados
- Deploy em produção

## 📚 Documentação

- **PROMPT.md**: Especificação original
- **REVISAO_SISTEMA.md**: Análise completa de implementação
- **API Docs**: http://localhost:8000/docs

## 🧪 Desenvolvimento

### Adicionar Nova Entidade
1. Criar modelo em `app/models/`
2. Criar schema em `app/schemas/`
3. Criar rotas em `app/routes/`
4. Registrar em `app/main.py`

### Migrações de Banco
```bash
alembic revision --autogenerate -m "Descrição"
alembic upgrade head
```

## 🤝 Contribuindo

1. Fork o projeto
2. Crie sua branch (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

## � Problemas Conhecidos

- Handsontable somente leitura
- Filtros parciais
- Validações de negócio faltando

Ver `REVISAO_SISTEMA.md` para lista completa.

## �📄 Licença

MIT License - veja arquivo LICENSE para detalhes.

---

**Desenvolvido com ❤️ usando FastAPI + TailwindCSS + Handsontable + Chart.js**  
**Status**: 🟡 Desenvolvimento  |  **Versão**: 1.0.0-alpha  |  **Atualizado**: 20/10/2025