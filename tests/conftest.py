import os
import pytest
from sqlalchemy import create_engine

# Configurar variables de entorno ANTES de importar la aplicación
os.environ['DATABASE_URL'] = 'sqlite:///./test.db'
os.environ['APP_ENV'] = 'test'
os.environ['SECRET_KEY'] = 'a_test_secret' # Chave secreta para ambiente de teste
# Ahora importar después de configurar las variables
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import engine, Base, SessionLocal
from app.models.usuario import Usuario
from app.core.auth import get_password_hash

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    # Recrear engine con la nueva URL
    from app.core import database
    database.engine = create_engine(os.environ['DATABASE_URL'])

    # Crear tablas
    Base.metadata.create_all(bind=database.engine)

    # Criar usuário admin para teste
    db = SessionLocal()
    existing_admin = db.query(Usuario).filter(Usuario.username == "admin").first()
    if not existing_admin:
        hashed_password = get_password_hash("admin123")
        admin_user = Usuario(
            nome="Administrador",
            email="admin@test.com",
            username="admin",
            hashed_password=hashed_password,
            tipo="administrador"
        )
        db.add(admin_user)
        db.commit()
    db.close()

@pytest.fixture
def client():
    return TestClient(app)