
import argparse
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Adiciona o diretório raiz do projeto ao sys.path para encontrar os módulos da aplicação
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.append(project_root)

try:
    from app.models.usuario import Usuario
    from app.core.auth import get_password_hash
except ImportError as e:
    print(f"Erro: Não foi possível importar os módulos da aplicação: {e}")
    print("Verifique se o script está no diretório raiz do projeto 'AlugueisV4' e se a estrutura de pastas está correta.")
    """DEPRECATED: movido para scripts/create_admin_user.py

    Shim compatível que executa o script movido.
    """
    from scripts.create_admin_user import main


    if __name__ == "__main__":
        main()
):
