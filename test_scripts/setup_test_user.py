#!/usr/bin/env python3
"""
Script para recriar tabelas e adicionar usuário de teste
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, Base
from app.models.usuario import Usuario
from app.core.auth import get_password_hash
from sqlalchemy.orm import sessionmaker

def main():
    print("Criando tabelas...")
    Base.metadata.create_all(bind=engine)
    print("Tabelas criadas!")

    # Criar sessão
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Criar usuário de teste (usando hash simples por enquanto)
        from passlib.hash import pbkdf2_sha256
        hashed_password = pbkdf2_sha256.hash("123")
        usuario_teste = Usuario(
            username="admin",
            nome="Administrador",
            tipo="administrador",
            email="admin@teste.com",
            telefone="(11) 99999-9999",
            hashed_password=hashed_password,
            ativo=True
        )

        db.add(usuario_teste)
        db.commit()
        print("Usuário de teste criado:")
        print("Username: admin")
        print("Password: 123")
        print("Email: admin@teste.com")

    except Exception as e:
        print(f"Erro ao criar usuário: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
