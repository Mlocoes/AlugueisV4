#!/usr/bin/env python3
"""
Script para limpar todos os registros de aluguéis mensais
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_login():
    """Fazer login e obter token"""
    login_data = {
        "username": "admin@example.com",
        "password": "admin00"
    }

    response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"❌ Erro no login: {response.status_code}")
        return None

def clear_all_rentals(token):
    """Limpar todos os registros de aluguéis mensais"""
    headers = {"Authorization": f"Bearer {token}"}

    print("🧹 Limpando todos os aluguéis mensais...")

    # Buscar todos os aluguéis mensais
    response = requests.get(f"{BASE_URL}/api/alugueis/mensais/?limit=10000", headers=headers)

    if response.status_code != 200:
        print(f"❌ Erro ao buscar aluguéis: {response.status_code}")
        return False

    rentals = response.json()
    total_rentals = len(rentals)

    if total_rentals == 0:
        print("✅ Não há aluguéis para limpar.")
        return True

    print(f"  Encontrados {total_rentals} registros de aluguéis")

    deleted_count = 0
    for rental in rentals:
        delete_response = requests.delete(
            f"{BASE_URL}/api/alugueis/mensais/{rental['id']}",
            headers=headers
        )

        if delete_response.status_code == 200:
            deleted_count += 1
            if deleted_count % 100 == 0:  # Mostrar progresso a cada 100
                print(f"  🗑️  Deletados {deleted_count}/{total_rentals} registros...")
        else:
            print(f"  ❌ Erro ao deletar ID {rental['id']}: {delete_response.status_code}")

    print(f"  ✅ Deletados {deleted_count} registros de aluguéis")
    return True

def verify_cleanup(token):
    """Verificar se a limpeza foi bem-sucedida"""
    headers = {"Authorization": f"Bearer {token}"}

    print("\n🔍 Verificando limpeza...")

    response = requests.get(f"{BASE_URL}/api/alugueis/mensais/?limit=10", headers=headers)

    if response.status_code == 200:
        rentals = response.json()
        remaining = len(rentals)
        print(f"  Registros restantes: {remaining}")

        if remaining == 0:
            print("  ✅ Todos os aluguéis foram removidos com sucesso!")
            return True
        else:
            print(f"  ⚠️  Ainda restam {remaining} registros. Verifique manualmente.")
            return False
    else:
        print(f"❌ Erro ao verificar: {response.status_code}")
        return False

def main():
    print("🧹 Limpando TODOS os registros de aluguéis mensais...")

    # Login
    token = test_login()
    if not token:
        return

    # Confirmar ação perigosa
    print("\n⚠️  ATENÇÃO: Esta ação irá deletar TODOS os aluguéis mensais!")
    confirm = input("Digite 'SIM' para confirmar: ")
    if confirm != 'SIM':
        print("❌ Operação cancelada pelo usuário.")
        return

    # Limpar todos os aluguéis
    if not clear_all_rentals(token):
        return

    # Verificar limpeza
    if verify_cleanup(token):
        print("\n✅ Todos os aluguéis foram removidos com sucesso!")
        print("💡 O banco de dados está limpo e pronto para novas importações.")
    else:
        print("\n⚠️ Verifique se todos os registros foram removidos.")

if __name__ == "__main__":
    main()