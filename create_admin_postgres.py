import sys
import os
from sqlalchemy.orm import sessionmaker

# Adiciona o diretório raiz do projeto ao sys.path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.append(project_root)

try:
    from app.models.usuario import Usuario
    from app.core.auth import get_password_hash
    from app.core.database import engine
except ImportError as e:
    print(f"Erro: Não foi possível importar os módulos da aplicação: {e}")
    sys.exit(1)

def create_admin_user():
    """Cria um usuário administrador padrão no banco de dados."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Verificar se já existe um admin
        existing_admin = db.query(Usuario).filter(Usuario.tipo == 'administrador').first()
        if existing_admin:
            print("✅ Já existe um usuário administrador no sistema.")
            print(f"  - Email: {existing_admin.email}")
            print(f"  - Nome: {existing_admin.nome}")
            return

        # Dados do admin padrão
        nome = "Administrador"
        email = "admin@alugueis.com"
        password = "admin123"
        username = "admin"

        # Verificar se username já existe
        existing_user = db.query(Usuario).filter(Usuario.username == username).first()
        if existing_user:
            print(f"❌ Erro: Username '{username}' já existe.")
            return

        # Criptografar a senha
        hashed_password = get_password_hash(password)

        # Criar o usuário administrador
        new_admin = Usuario(
            nome=nome,
            email=email,
            username=username,
            hashed_password=hashed_password,
            tipo='administrador',
            ativo=True
        )

        db.add(new_admin)
        db.commit()

        print("✅ Usuário administrador criado com sucesso!")
        print(f"  - Nome: {nome}")
        print(f"  - Email: {email}")
        print(f"  - Username: {username}")
        print(f"  - Senha: {password}")
        print("\n🔐 Use essas credenciais para fazer login no sistema.")

    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao criar usuário administrador: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()