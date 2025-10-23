# Migração para PostgreSQL

Este documento descreve a migração do banco de dados SQLite para PostgreSQL usando Docker.

## Arquitetura

- **PostgreSQL**: Banco de dados principal em contêiner Docker
- **Aplicação**: FastAPI rodando em contêiner Docker conectando ao PostgreSQL

## Serviços Docker

### PostgreSQL
- **Imagem**: `postgres:15`
- **Banco**: `alugueis`
- **Usuário**: `alugueis_user`
- **Senha**: `alugueis_password`
- **Porta**: `5432`

### Aplicação
- **Porta**: `8000`
- **Dependência**: PostgreSQL saudável

## Como usar

### 1. Iniciar serviços
```bash
docker-compose up -d
```

### 2. Verificar status
```bash
docker-compose ps
```

### 3. Logs
```bash
docker-compose logs -f
```

### 4. Parar serviços
```bash
docker-compose down
```

## Migração de Dados

A migração foi realizada do SQLite (`alugueis.db`) para PostgreSQL usando o script `migrate_to_postgres.py`.

### Dados migrados:
- **15 usuários**
- **22 imóveis**
- **1620 aluguéis mensais**
- **161 participações**

### Problemas resolvidos:
- Conversão de tipos booleanos (SQLite usa inteiros, PostgreSQL usa booleanos)
- Truncamento de valores numéricos muito grandes
- Mapeamento de nomes de colunas entre esquemas diferentes

## Configuração

### Ambiente da aplicação
```yaml
environment:
  - DATABASE_URL=postgresql://alugueis_user:alugueis_password@db:5432/alugueis
  - SECRET_KEY=your-secret-key-here
```

### Conexão com PostgreSQL
- **Host**: `db` (nome do serviço no Docker Compose)
- **Porta**: `5432`
- **Database**: `alugueis`

## Desenvolvimento Local

Para desenvolvimento local, altere a `DATABASE_URL` em `app/core/config.py`:

```python
database_url: str = "postgresql://alugueis_user:alugueis_password@localhost:5432/alugueis"
```

## Backup e Restauração

### Backup
```bash
docker exec -t alugueisv4-db-1 pg_dump -U alugueis_user -d alugueis > backup.sql
```

### Restauração
```bash
docker exec -i alugueisv4-db-1 psql -U alugueis_user -d alugueis < backup.sql
```

## Monitoramento

### Health Check
O PostgreSQL tem health check configurado:
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U alugueis_user -d alugueis"]
```

### Logs
```bash
# Logs do PostgreSQL
docker-compose logs db

# Logs da aplicação
docker-compose logs app
```