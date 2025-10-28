# Etapa 1: Builder - Instala as dependências
FROM python:3.11-slim as builder

WORKDIR /app

# Instalar dependências de build, se necessário
# RUN apt-get update && apt-get install -y --no-install-recommends gcc

# Criar um ambiente virtual
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copiar e instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Etapa 2: Final - Cria a imagem de produção
FROM python:3.11-slim

# Instalar cliente PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client && rm -rf /var/lib/apt/lists/*

# Criar usuário não-root
RUN groupadd -r appuser -g 1000 && useradd -r -g appuser -u 1000 appuser
WORKDIR /app

# Copiar o ambiente virtual da etapa de build
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copiar o código da aplicação
COPY . .

# Mudar propriedade dos arquivos para o usuário não-root
RUN chown -R appuser:appuser /app

# Mudar para usuário não-root
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
