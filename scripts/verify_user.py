
import argparse
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Adiciona o diretório raiz do projeto ao sys.path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.append(project_root)

try:
    from app.models.usuario import Usuario
except ImportError as e:
    print(f"Erro ao importar módulos: {e}")
    sys.exit(1)

def verify_user(db_path: str, email: str):
    """Verifica e exibe os detalhes de um usuário no banco de dados."""
    database_url = f"sqlite:///{db_path}"
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        print(f"Buscando usuário com email: {email}...")
        user = db.query(Usuario).filter(Usuario.email == email).first()

        if not user:
            print("\n❌ Usuário não encontrado.")
            return

        print("\n✅ Usuário encontrado!")
        print("------------------------")
        print(f"  ID:       {user.id}")
        print(f"  Nome:     {user.nome}")
        print(f"  Username: {user.username}")
        print(f"  Email:    {user.email}")
        print(f"  Tipo:     {user.tipo}")
        print(f"  Ativo:    {user.ativo}")
        print(f"  Senha Hashed: {user.hashed_password[:30]}...") # Mostra apenas o início do hash

    except Exception as e:
        print(f"\n❌ Erro ao consultar o banco de dados: {e}")
    finally:
        db.close()

def main():
    parser = argparse.ArgumentParser(description="Verifica um usuário no banco de dados do AlugueisV4.")
    parser.add_argument("email", help="Email do usuário a ser verificado.")
    args = parser.parse_args()

    db_path = os.path.join(project_root, 'alugueis.db')

    if not os.path.exists(db_path):
        print(f"Erro: Arquivo de banco de dados 'alugueis.db' não encontrado em {project_root}")
        sys.exit(1)

    verify_user(db_path, args.email)

if __name__ == "__main__":
    main()
