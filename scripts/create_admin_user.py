import argparse
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Adiciona o diretório raiz do projeto ao sys.path para encontrar os módulos da aplicação
project_root = os.path.abspath(os.path.dirname(__file__) + '/../')
sys.path.append(project_root)

try:
    from app.models.usuario import Usuario
    from app.core.auth import get_password_hash
except ImportError as e:
    print(f"Erro: Não foi possível importar os módulos da aplicação: {e}")
    print("Verifique se o script está no diretório raiz do projeto 'AlugueisV4' e se a estrutura de pastas está correta.")
    sys.exit(1)

def create_admin(
    db_path: str,
    nome: str,
    email: str,
    password: str,
    documento: str = None,
    telefone: str = None
):
    """Cria um novo usuário administrador no banco de dados."""
    database_url = f"sqlite:///{db_path}"
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Verificar se o usuário já existe
        existing_user = db.query(Usuario).filter(Usuario.email == email).first()
        if existing_user:
            print(f"❌ Erro: Já existe um usuário com o email '{email}'. Operação cancelada.")
            return

        # Criptografar a senha
        hashed_password = get_password_hash(password)

        # Criar o novo usuário administrador
        new_admin = Usuario(
            nome=nome,
            email=email,
            username=email,  # Usar email como nome de usuário por padrão
            hashed_password=hashed_password,
            tipo='administrador',
            ativo=True,
            documento=documento,
            telefone=telefone
        )

        db.add(new_admin)
        db.commit()

        print("✅ Usuário administrador criado com sucesso!")
        print(f"  - Nome: {nome}")
        print(f"  - Email/Username: {email}")
        print(f"  - Senha: {password}")

    except Exception as e:
        db.rollback()
        print(f"❌ Erro inesperado ao criar usuário: {e}")
    finally:
        db.close()

def main():
    parser = argparse.ArgumentParser(
        description="Cria um novo usuário administrador para o sistema AlugueisV4.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("nome", help="Nome completo do usuário.")
    parser.add_argument("email", help="Email do usuário (será usado como username para login).")
    parser.add_argument("--senha", default="123", help="Senha para o novo usuário (padrão: '123').")
    parser.add_argument("--documento", default=None, help="(Opcional) Documento do usuário (CPF/CNPJ).")
    parser.add_argument("--telefone", default=None, help="(Opcional) Telefone de contato do usuário.")

    args = parser.parse_args()

    # Constrói o caminho absoluto para o arquivo de banco de dados
    db_path = os.path.join(project_root, 'alugueis.db')

    if not os.path.exists(db_path):
        print(f"Erro: O arquivo de banco de dados 'alugueis.db' não foi encontrado em:")
        print(project_root)
        sys.exit(1)

    create_admin(
        db_path=db_path,
        nome=args.nome,
        email=args.email,
        password=args.senha,
        documento=args.documento,
        telefone=args.telefone
    )

if __name__ == "__main__":
    main()
