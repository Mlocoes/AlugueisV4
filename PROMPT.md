________________________________________
🚀 PROMPT COMPLETO — Claude 4.5 (para Visual Studio Code)
Use este prompt diretamente em Claude 4.5 dentro do VS Code.
Ele já vem com instruções para gerar código Python (FastAPI + SQLAlchemy + PostgreSQL) e frontend com Handsontable.
O fluxo é interativo, e Claude vai codificar etapa por etapa.
________________________________________
🧠 Contexto e Objetivo
Você é um engenheiro de software sênior especializado em desenvolvimento Python com FastAPI, SQLAlchemy e PostgreSQL, e integração com frontend moderno (Handsontable + TailwindCSS + Chart.js).
Sua tarefa é gerar, de forma interativa e modular, uma aplicação completa de gestão de imóveis e aluguéis, com controle de permissões financeiras definido por administradores.
O sistema será codificado dentro do Visual Studio Code, e o código deve estar organizado, comentado e pronto para execução com Docker Compose.
________________________________________
⚙️ Especificações Técnicas
Backend:
•	Linguagem: Python 3.11+
•	Framework: FastAPI
•	ORM: SQLAlchemy 2.0
•	DB: PostgreSQL
•	Migrações: Alembic
•	Autenticação: JWT (PyJWT)
•	Senhas: Passlib (bcrypt)
•	Testes: pytest
•	Containers: Docker + docker-compose
Frontend:
•	HTML + TailwindCSS
•	Handsontable para tabelas e edição
•	Chart.js para gráficos
•	JS Fetch para consumir a API
•	Design responsivo para desktop e móvel
________________________________________
🧩 Estrutura da Base de Dados
Crie os seguintes modelos com SQLAlchemy:
usuarios
•	id (PK)
•	nome
•	tipo (Administrador | Usuário)
•	email (único)
•	telefone
•	senha_hash
•	ativo (bool)
imoveis
•	id (PK)
•	nome
•	endereco
•	alugado (bool)
•	ativo (bool)
participacoes
•	id (PK)
•	id_imovel (FK → imoveis.id)
•	id_proprietario (FK → usuarios.id)
•	participacao (float)
→ soma total por imóvel deve ser 100 ± 0.4%
•	data_cadastro (timestamp, grupo único de versão)
alugueis
•	id (PK)
•	id_imovel (FK → imoveis.id)
•	id_proprietario (FK → usuarios.id)
•	valor_liquido (float, pode ser negativo)
•	darf (float opcional)
•	data_cadastro (timestamp)
alias
•	id (PK)
•	nome
•	ativo (bool)
alias_proprietarios
•	id (PK)
•	id_alias (FK → alias.id)
•	id_proprietario (FK → usuarios.id)
transferencias
•	id (PK)
•	id_alias (FK → alias.id)
•	id_proprietario (FK → usuarios.id)
•	valor (float)
•	data_inicio
•	data_fim
permissoes_financeiras
•	id (PK)
•	id_admin (FK → usuarios.id, tipo=Administrador)
•	id_usuario (FK → usuarios.id, tipo=Usuário)
•	id_proprietario_autorizado (FK → usuarios.id, tipo=Proprietário)
________________________________________
🔒 Controle de Acesso
•	Somente administradores podem criar, editar ou excluir registros.
•	Usuários comuns:
o	Não veem dados inativos.
o	Só veem informações financeiras dos proprietários definidos em permissoes_financeiras.
o	Não têm botões de edição ou criação.
________________________________________
💰 Regras de Negócio
•	Soma das participações por imóvel = 100 ± 0.4 %
•	taxa_admin_proprietario = taxa_admin_total * (participacao / 100)
•	Aluguel total anual = soma dos aluguéis do ano corrente
•	Se flag “Transferências” estiver ativo, somar aluguel + transferência no relatório
________________________________________
🖥️ Telas e Funcionalidades
🔐 Login
•	Tela simples com email + senha
•	Autenticação via JWT
•	Sessão expira após tempo configurável
•	Recarregar = volta ao login
🏠 Dashboard
•	Menu lateral persistente
•	Mostra:
o	Nº imóveis alugados
o	Nº imóveis disponíveis
o	Valor acumulado do ano
o	Valor do último mês
o	Variação percentual mês a mês
o	Gráfico mensal (Chart.js)
👤 Proprietários
•	Tabela (Handsontable)
•	Botões: Novo / Editar (somente admin)
•	Ocultar IDs
•	Usuários comuns: somente visualização
🏢 Imóveis
•	Tabela (Handsontable)
•	Botões: Novo / Editar (somente admin)
•	Filtro por status (alugado/disponível)
•	Usuários comuns: somente leitura
📊 Participações
•	Tabela (Handsontable):
o	Linhas = imóveis
o	Colunas = proprietários
o	Células = participações (%)
•	Botão “Editar” → mostra e permite editar todas as participações de um imóvel
•	Verificação automática: soma = 100 ± 0.4%
•	Combo para escolher versão (data_cadastro)
💵 Aluguel
•	Tabela (Handsontable):
o	Linhas = imóveis
o	Colunas = proprietários
o	Células = valor_liquido
•	Filtros:
o	Ano (padrão = último cadastrado)
o	Mês (padrão = último cadastrado ou “Todos”)
•	“Todos os meses” → soma acumulada
📈 Relatórios
•	Colunas: Aluguel | Darf | Taxa de Administração
•	Filtros:
o	Ano
o	Mês
o	Proprietário / Alias
o	Flag “Transferências” → soma aluguel + transferência
•	Dados filtrados e limitados pelas permissões do usuário
⚙️ Administração
•	Botões:
o	Novo Alias / Editar Alias
o	Nova Transferência / Editar Transferência
o	Importar Excel (via pandas)
•	Upload → validação e inserção automática
________________________________________
🧭 Fluxo de Desenvolvimento (Claude deve seguir)
1.	Confirmar stack (FastAPI + SQLAlchemy + PostgreSQL)
2.	Gerar estrutura de diretórios:
3.	app/
4.	  ├── main.py
5.	  ├── models/
6.	  ├── routes/
7.	  ├── schemas/
8.	  ├── services/
9.	  ├── core/ (config, segurança, auth)
10.	  ├── static/
11.	  └── templates/
12.	Gerar models e schemas
13.	Gerar endpoints REST
14.	Adicionar autenticação JWT
15.	Implementar middleware de autorização (baseado em permissões financeiras)
16.	Gerar frontend básico com Handsontable
17.	Conectar frontend com backend
18.	Criar gráfico do dashboard
19.	Gerar migrações Alembic
20.	Criar docker-compose.yml (FastAPI + PostgreSQL)
21.	Adicionar scripts de teste (pytest)
________________________________________
🔁 Interatividade
Antes de gerar cada parte, pergunte:
“Deseja que eu gere esta parte agora (Sim/Não)?”
Etapas interativas recomendadas:
1.	Modelos e migrações
2.	Rotas e autenticação
3.	Dashboard e frontend básico
4.	Controle de permissões financeiras
5.	Relatórios e gráficos
6.	Deploy (Docker)
________________________________________
🧩 Resultado Esperado
Uma aplicação modular, segura e responsiva, com:
•	Controle de acesso granular a dados financeiros
•	Interface editável via Handsontable
•	Dashboards e relatórios dinâmicos
•	Backend em Python/FASTAPI pronto para produção
•	Compatibilidade total com dispositivos móveis
________________________________________
🧾 Instrução final para Claude 4.5
Gere o código de forma modular, começando pela estrutura do projeto e modelos SQLAlchemy.
Pergunte antes de avançar para cada módulo seguinte.
Organize o código em diretórios prontos para rodar no VS Code com uvicorn main:app --reload.
Inclua comentários explicativos e docstrings em todas as classes e funções.
________________________________________

📋 STATUS DA IMPLEMENTAÇÃO - AlugueisV4
Data: 20 de Outubro de 2025

✅ IMPLEMENTADO (60% do PROMPT.md)
- ✅ Estrutura de diretórios completa (app/models, routes, schemas, services, etc.)
- ✅ 8 Modelos SQLAlchemy (Usuario, Imovel, Participacao, Aluguel, Alias, Transferencia, PermissaoFinanceira, AliasProprietario)
- ✅ 9 Routers FastAPI com autenticação JWT
- ✅ 9 Páginas HTML com TailwindCSS
- ✅ JavaScript modular com ApiClient
- ✅ CRUD completo para todas entidades
- ✅ Dashboard com Chart.js
- ✅ Handsontable para tabelas
- ✅ SQLite (desenvolvimento) + Alembic
- ✅ Docker e docker-compose

⚠️ IMPLEMENTADO PARCIALMENTE (30%)
- ⚠️ Controle de acesso (estrutura existe, lógica não implementada)
- ⚠️ Validações de regras de negócio (básicas apenas)
- ⚠️ Frontend editável (somente leitura em alguns lugares)
- ⚠️ Filtros avançados (estrutura básica)
- ⚠️ Relatórios (template existe, funcionalidade limitada)

❌ NÃO IMPLEMENTADO (10%)
- ❌ PostgreSQL (usando SQLite)
- ❌ Importação de Excel
- ❌ Exportação de relatórios
- ❌ Testes pytest
- ❌ Validação automática soma participações = 100%
- ❌ Cálculos automáticos de taxas
- ❌ Sistema de versões de participações
- ❌ Permissões granulares por usuário
- ❌ Responsividade mobile completa

📖 DOCUMENTAÇÃO ADICIONAL
Veja REVISAO_SISTEMA.md para análise completa e próximos passos recomendados.

🚀 COMO USAR O SISTEMA ATUAL
1. Instalar dependências: pip install -r requirements.txt
2. Iniciar servidor: uvicorn app.main:app --reload
3. Acessar: http://localhost:8000
4. Login automático com: admin / 123

⚠️ AVISO: Sistema funcional mas NÃO pronto para produção.
Faltam validações críticas e controle de acesso.
________________________________________
-- =========================================
-- 1️⃣ Tabela de Usuários / Proprietários
-- =========================================
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(120) NOT NULL,
    tipo VARCHAR(20) CHECK (tipo IN ('administrador', 'usuario')) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    telefone VARCHAR(20),
    ativo BOOLEAN DEFAULT TRUE
);

-- =========================================
-- 2️⃣ Tabela de Imóveis
-- =========================================
CREATE TABLE imoveis (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(120) NOT NULL,
    endereco TEXT NOT NULL,
    alugado BOOLEAN DEFAULT FALSE,
    ativo BOOLEAN DEFAULT TRUE
);

-- =========================================
-- 3️⃣ Tabela de Participações
-- =========================================
-- Guarda o percentual de cada proprietário em cada imóvel.
-- Vários registros podem coexistir com diferentes datas de cadastro (histórico).
CREATE TABLE participacoes (
    id SERIAL PRIMARY KEY,
    id_imovel INTEGER REFERENCES imoveis(id) ON DELETE CASCADE,
    id_proprietario INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
    participacao NUMERIC(6,3) CHECK (participacao >= 0 AND participacao <= 100),
    data_cadastro DATE NOT NULL,
    UNIQUE (id_imovel, id_proprietario, data_cadastro)
);

-- Índice para facilitar filtragem por data
CREATE INDEX idx_participacoes_data ON participacoes (data_cadastro);

-- =========================================
-- 4️⃣ Tabela de Aluguéis
-- =========================================
-- Armazena valores líquidos por proprietário e imóvel.
CREATE TABLE alugueis (
    id SERIAL PRIMARY KEY,
    id_imovel INTEGER REFERENCES imoveis(id) ON DELETE CASCADE,
    id_proprietario INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
    aluguel_liquido NUMERIC(12,2) DEFAULT 0,
    taxa_administracao_total NUMERIC(6,2) DEFAULT 0,
    darf NUMERIC(12,2) DEFAULT 0,
    data_cadastro DATE NOT NULL
);

-- Índices de performance
CREATE INDEX idx_alugueis_data ON alugueis (data_cadastro);
CREATE INDEX idx_alugueis_imovel_prop ON alugueis (id_imovel, id_proprietario);

-- =========================================
-- 5️⃣ Tabela de Aliases (grupos de proprietários)
-- =========================================
CREATE TABLE alias (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(120) NOT NULL,
    ativo BOOLEAN DEFAULT TRUE
);

-- Relação N:N entre Aliases e Proprietários
CREATE TABLE alias_proprietarios (
    id_alias INTEGER REFERENCES alias(id) ON DELETE CASCADE,
    id_proprietario INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
    PRIMARY KEY (id_alias, id_proprietario)
);

-- =========================================
-- 6️⃣ Tabela de Transferências
-- =========================================
CREATE TABLE transferencias (
    id SERIAL PRIMARY KEY,
    id_alias INTEGER REFERENCES alias(id) ON DELETE CASCADE,
    id_proprietario INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
    valor NUMERIC(12,2) DEFAULT 0,
    data_inicio DATE NOT NULL,
    data_fim DATE
);

CREATE INDEX idx_transferencias_periodo ON transferencias (data_inicio, data_fim);

-- =========================================
-- 7️⃣ Tabela de Permissões Financeiras
-- =========================================
-- Define o que cada usuário pode ver/editar em termos de dados financeiros.
CREATE TABLE permissoes_financeiras (
    id SERIAL PRIMARY KEY,
    id_usuario INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
    id_proprietario INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
    visualizar BOOLEAN DEFAULT TRUE,
    editar BOOLEAN DEFAULT FALSE,
    data_criacao TIMESTAMP DEFAULT NOW(),
    UNIQUE (id_usuario, id_proprietario)
);

CREATE INDEX idx_perm_fin_usuario_prop ON permissoes_financeiras (id_usuario, id_proprietario);

-- =========================================
-- 8️⃣ View auxiliar para cálculo da Taxa de Administração individual
-- =========================================
CREATE OR REPLACE VIEW vw_taxa_admin_proprietario AS
SELECT 
    a.id AS id_aluguel,
    a.id_imovel,
    a.id_proprietario,
    a.aluguel_liquido,
    p.participacao,
    (a.taxa_administracao_total * (p.participacao / 100.0)) AS taxa_admin_prop
FROM alugueis a
JOIN participacoes p
  ON a.id_imovel = p.id_imovel
  AND a.id_proprietario = p.id_proprietario
  AND p.data_cadastro = (
      SELECT MAX(data_cadastro) 
      FROM participacoes 
      WHERE id_imovel = a.id_imovel 
        AND id_proprietario = a.id_proprietario
  );

