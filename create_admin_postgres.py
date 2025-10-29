"""DEPRECATED: movido para scripts/create_admin_postgres.py

Este arquivo é um shim compatível que executa o script movido.
"""
from scripts.create_admin_postgres import create_admin_user


if __name__ == "__main__":
    create_admin_user()