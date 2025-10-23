#!/usr/bin/env python3
"""
Script para limpar dados de aluguéis mensais incorretos e reimportar
"""
import requests
import json
from decimal import Decimal

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

def clear_incorrect_data(token):
    """Limpar dados de aluguéis mensais com valores incorretos"""
    headers = {"Authorization": f"Bearer {token}"}

    print("🧹 Limpando dados incorretos...")

    # Buscar todos os aluguéis mensais
    response = requests.get(f"{BASE_URL}/api/alugueis/mensais/?limit=1000", headers=headers)

    if response.status_code != 200:
        print(f"❌ Erro ao buscar dados: {response.status_code}")
        return False

    rentals = response.json()
    print(f"  Encontrados {len(rentals)} registros")

    deleted_count = 0
    for rental in rentals:
        valor_total = rental.get('valor_total', 0)
        valor_proprietario = rental.get('valor_proprietario', 0)

        # Considerar incorretos valores maiores que 100 mil (valores normais de aluguel são menores)
        if valor_total > 100000 or valor_proprietario > 100000:
            delete_response = requests.delete(
                f"{BASE_URL}/api/alugueis/mensais/{rental['id']}",
                headers=headers
            )

            if delete_response.status_code == 200:
                deleted_count += 1
                print(f"  🗑️  Deletado ID {rental['id']}: R$ {valor_total:,.2f}")
            else:
                print(f"  ❌ Erro ao deletar ID {rental['id']}: {delete_response.status_code}")

    print(f"  ✅ Deletados {deleted_count} registros incorretos")
    return True

def verify_data_clean(token):
    """Verificar se os dados foram limpos"""
    headers = {"Authorization": f"Bearer {token}"}

    print("\n🔍 Verificando limpeza...")

    response = requests.get(f"{BASE_URL}/api/alugueis/mensais/?limit=1000", headers=headers)

    if response.status_code == 200:
        rentals = response.json()
        print(f"  Registros restantes: {len(rentals)}")

        if rentals:
            print("  Verificando valores restantes:")
            for rental in rentals[:5]:
                valor_total = rental.get('valor_total', 0)
                if valor_total > 1000000:
                    print(f"    ⚠️  Ainda há valor alto: ID {rental['id']} - R$ {valor_total:,.2f}")
                else:
                    print(f"    ✅ Valor OK: ID {rental['id']} - R$ {valor_total:,.2f}")

        return len(rentals) == 0 or all(r.get('valor_total', 0) <= 1000000 for r in rentals)
    else:
        print(f"❌ Erro ao verificar: {response.status_code}")
        return False

def main():
    print("🧹 Limpando dados de aluguéis mensais incorretos...")

    # Login
    token = test_login()
    if not token:
        return

    # Limpar dados incorretos
    if not clear_incorrect_data(token):
        return

    # Verificar limpeza
    if verify_data_clean(token):
        print("\n✅ Dados limpos com sucesso!")
        print("💡 Agora você pode reimportar o arquivo Excel com os valores corretos.")
    else:
        print("\n⚠️ Ainda há dados incorretos. Verifique manualmente.")

if __name__ == "__main__":
    main()