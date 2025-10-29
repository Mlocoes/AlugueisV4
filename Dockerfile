# Stage: assets - build frontend assets (Tailwind CSS) using Node
FROM node:18-alpine as assets

WORKDIR /src

# Copy only what is needed for building the CSS
COPY package.json package-lock.json* ./
COPY tailwind.config.js postcss.config.js ./
COPY src ./src

# Install node deps and build the CSS
RUN npm ci --no-audit --no-fund || npm install
RUN npm run build:css


# Etapa: Builder - Instala as dependências Python em um venv
FROM python:3.11-slim as builder

WORKDIR /app

# Criar um ambiente virtual
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copiar e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Etapa Final - Cria a imagem de produção
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

# Copiar o CSS compilado do stage `assets` (se existir)
COPY --from=assets /src/app/static/css/tailwind.css ./app/static/css/tailwind.css

# Mudar propriedade dos arquivos para o usuário não-root
RUN chown -R appuser:appuser /app

# Mudar para usuário não-root
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
