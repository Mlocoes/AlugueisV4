#!/bin/bash

# Script para executar migrações no banco de dados

cd /home/mloco/Escritorio/AlugueisV4

# Aguardar o banco estar pronto
echo "Aguardando banco de dados..."
sleep 5

# Executar migração
source venv/bin/activate
python -c "
from app.core.database import engine, Base
Base.metadata.create_all(bind=engine)
print('Tabelas criadas com sucesso!')
"