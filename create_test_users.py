#!/usr/bin/env python3
"""
Script para criar usuários de teste no banco de dados
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.core.database import SessionLocal
from app.models.usuario import Usuario
from app.core.auth import get_password_hash

def create_test_users():
    db = SessionLocal()
    try:
        # Verificar se já existem usuários
        existing = db.query(Usuario).count()
        if existing > 0:
            print(f"Já existem {existing} usuários no banco")
            return

        # Criar admin
        admin = Usuario(
            username='admin',
            nome='Administrador',
            email='admin@example.com',
            tipo='administrador',
            hashed_password=get_password_hash('admin00'),
            ativo=True
        )
        db.add(admin)
        db.commit()
        print('✅ Usuário admin criado: admin / admin00')

        # Criar usuário comum
        user = Usuario(
            username='user',
            nome='Usuário Comum',
            email='user@example.com',
            tipo='usuario',
            hashed_password=get_password_hash('123456'),
            ativo=True
        )
        db.add(user)
        db.commit()
        print('✅ Usuário comum criado: user / 123456')

    except Exception as e:
        print(f'❌ Erro: {e}')
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_users()