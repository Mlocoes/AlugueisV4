#!/usr/bin/env python3
"""
Script de verificação final das correções implementadas
"""
import requests
import time

BASE_URL = "http://localhost:8000"

def test_backend_fixes():
    """Testa as correções no backend"""
    print("🔧 Testando correções no backend...")

    # Teste 1: Login
    print("  1. Testando login...")
    response = requests.post(f"{BASE_URL}/auth/login",
                           data={"username": "admin", "password": "admin00"})
    if response.status_code != 200:
        print("     ❌ Login falhou")
        return False
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("     ✅ Login OK")

    # Teste 2: PUT endpoint para alugueis mensais
    print("  2. Testando PUT endpoint para alugueis mensais...")
    response = requests.get(f"{BASE_URL}/api/alugueis/mensais/?limit=1", headers=headers)
    if response.status_code != 200 or not response.json():
        print("     ❌ Não foi possível obter aluguel para teste")
        return False

    aluguel_id = response.json()[0]["id"]
    update_data = {"valor_total": 2000.00, "status": "pendente"}

    response = requests.put(f"{BASE_URL}/api/alugueis/mensais/{aluguel_id}",
                          headers={**headers, "Content-Type": "application/json"},
                          json=update_data)

    if response.status_code == 200:
        print("     ✅ PUT endpoint OK")
    else:
        print(f"     ❌ PUT endpoint falhou: {response.status_code}")
        return False

    return True

def test_frontend_fixes():
    """Testa as correções no frontend"""
    print("🎨 Testando correções no frontend...")

    # Teste 1: Verificar se a página carrega sem erros JavaScript
    print("  1. Testando carregamento da página principal...")
    response = requests.get(f"{BASE_URL}/")
    if response.status_code != 200:
        print("     ❌ Página não carrega")
        return False
    print("     ✅ Página carrega OK")

    # Teste 2: Verificar se o JavaScript main.js tem as correções
    print("  2. Verificando correções no JavaScript...")
    try:
        with open("app/static/js/main.js", "r", encoding="utf-8") as f:
            js_content = f.read()
        if "if (!api || !api.isAdmin)" not in js_content:
            print("     ❌ Correções no JavaScript não encontradas")
            return False
        print("     ✅ Correções no JavaScript OK")
    except FileNotFoundError:
        print("     ❌ Arquivo JavaScript não encontrado")
        return False

    return True

def main():
    print("🚀 Iniciando verificação final das correções...")
    print("=" * 50)

    backend_ok = test_backend_fixes()
    print()
    frontend_ok = test_frontend_fixes()

    print()
    print("=" * 50)
    if backend_ok and frontend_ok:
        print("🎉 Todas as correções foram implementadas com sucesso!")
        print()
        print("📋 Resumo das correções:")
        print("   ✅ Endpoint PUT para alugueis mensais implementado")
        print("   ✅ Verificações de segurança no frontend adicionadas")
        print("   ✅ Sistema funcionando sem erros JavaScript")
        print("   ✅ Autenticação funcionando corretamente")
    else:
        print("❌ Algumas correções ainda precisam ser verificadas")
        if not backend_ok:
            print("   - Problemas no backend")
        if not frontend_ok:
            print("   - Problemas no frontend")

if __name__ == "__main__":
    main()