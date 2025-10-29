#!/usr/bin/env python3
"""
Script para criar usuário administrador interativamente
"""
import argparse
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Adiciona o diretório raiz do projeto ao sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

try:
    from app.models.usuario import Usuario
    from app.core.auth import get_password_hash
    from app.core.database import get_db
except ImportError as e:
    print(f"Erro: Não foi possível importar os módulos da aplicação: {e}")
    print("Verifique se está executando do diretório scripts/")
    sys.exit(1)

def create_admin_user(nome, email, password, tipo='administrador'):
    """Cria um usuário administrador"""
    db = next(get_db())

    # Verifica se já existe usuário com este email
    existing_user = db.query(Usuario).filter(Usuario.email == email).first()
    if existing_user:
        print(f"❌ Usuário com email {email} já existe!")
        return False

    # Gera username automaticamente do email
    username = email.split('@')[0].lower()

    # Verifica se username já existe
    existing_username = db.query(Usuario).filter(Usuario.username == username).first()
    if existing_username:
        # Adiciona número se necessário
        counter = 1
        while db.query(Usuario).filter(Usuario.username == f"{username}{counter}").first():
            counter += 1
        username = f"{username}{counter}"

    # Cria o usuário
    hashed_password = get_password_hash(password)
    admin_user = Usuario(
        nome=nome,
        email=email,
        username=username,
        hashed_password=hashed_password,
        tipo=tipo,
        ativo=True
    )

    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    print("✅ Usuário administrador criado com sucesso!"    print(f"   Nome: {admin_user.nome}")
    print(f"   Email: {admin_user.email}")
    print(f"   Username: {admin_user.username}")
    print(f"   Tipo: {admin_user.tipo}")

    return True

def main():
    parser = argparse.ArgumentParser(description='Criar usuário administrador')
    parser.add_argument('--nome', required=True, help='Nome do usuário')
    parser.add_argument('--email', required=True, help='Email do usuário')
    parser.add_argument('--password', required=True, help='Senha do usuário')
    parser.add_argument('--tipo', default='administrador', help='Tipo do usuário (default: administrador)')

    args = parser.parse_args()

    try:
        success = create_admin_user(args.nome, args.email, args.password, args.tipo)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Erro ao criar usuário: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()