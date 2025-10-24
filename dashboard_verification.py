#!/usr/bin/env python3
"""
Script completo para verificação do Dashboard
Testa estatísticas, gráficos, endpoints e validação de dados
"""
import requests
import json
import time
from datetime import datetime, timedelta

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

def test_dashboard_stats(token):
    """Testar estatísticas do dashboard"""
    headers = {"Authorization": f"Bearer {token}"}

    print("📊 Testando estatísticas do dashboard...")

    start_time = time.time()
    response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
    response_time = time.time() - start_time

    if response.status_code == 200:
        stats = response.json()
        print(".2f")
        print("  📈 Estatísticas encontradas:")

        # Validar estrutura dos dados
        expected_fields = ['total_imoveis', 'receita_mensal', 'alugueis_ativos',
                          'proprietarios_ativos', 'taxa_ocupacao', 'total_usuarios']

        for field in expected_fields:
            if field in stats:
                value = stats[field]
                print(f"    ✅ {field}: {value}")
            else:
                print(f"    ❌ Campo faltando: {field}")

        return stats
    else:
        print(f"❌ Erro nas estatísticas: {response.status_code} - {response.text}")
        return None

def test_dashboard_charts(token):
    """Testar dados dos gráficos"""
    headers = {"Authorization": f"Bearer {token}"}

    print("\n📈 Testando dados dos gráficos...")

    start_time = time.time()
    response = requests.get(f"{BASE_URL}/api/dashboard/charts", headers=headers)
    response_time = time.time() - start_time

    if response.status_code == 200:
        charts = response.json()
        print(".2f")
        print("  📊 Gráficos disponíveis:")

        expected_charts = ['receita_por_mes', 'status_imoveis', 'distribuicao_tipos', 'receita_por_proprietario']

        for chart_name in expected_charts:
            if chart_name in charts:
                data = charts[chart_name]
                print(f"    ✅ {chart_name}: {len(data)} registros")
            else:
                print(f"    ❌ Gráfico faltando: {chart_name}")

        return charts
    else:
        print(f"❌ Erro nos gráficos: {response.status_code} - {response.text}")
        return None

def test_dashboard_page():
    """Testar se a página do dashboard está acessível"""
    print("\n🌐 Testando página do dashboard...")

    response = requests.get(f"{BASE_URL}/dashboard")
    if response.status_code == 200:
        content = response.text
        if "Dashboard" in content and "Estatísticas" in content:
            print("  ✅ Página do dashboard carregada com sucesso")
            return True
        else:
            print("  ❌ Página carregada mas conteúdo parece incompleto")
            return False
    else:
        print(f"❌ Erro ao carregar página: {response.status_code}")
        return False

def generate_report(stats, charts, page_ok):
    """Gerar relatório final"""
    print("\n" + "="*60)
    print("📋 RELATÓRIO FINAL - VERIFICAÇÃO DO DASHBOARD")
    print("="*60)

    # Status geral
    print("🎯 STATUS GERAL:")
    if stats and charts and page_ok:
        print("  ✅ Dashboard completamente funcional")
    else:
        print("  ❌ Dashboard com problemas")

    # Estatísticas principais
    if stats:
        print("\n📊 ESTATÍSTICAS PRINCIPAIS:")
        print(f"  • Total de imóveis: {stats.get('total_imoveis', 'N/A')}")
        print(f"  • Receita mensal: R$ {stats.get('receita_mensal', 0):,.2f}")
        print(f"  • Aluguéis ativos: {stats.get('alugueis_ativos', 'N/A')}")
        print(f"  • Taxa de ocupação: {stats.get('taxa_ocupacao', 0):.1f}%")
        print(f"  • Total de usuários: {stats.get('total_usuarios', 'N/A')}")

    # Gráficos
    if charts:
        print("\n📈 GRÁFICOS:")
        chart_info = [
            ('receita_por_mes', 'Receita por mês'),
            ('status_imoveis', 'Status dos imóveis'),
            ('distribuicao_tipos', 'Distribuição por tipo'),
            ('receita_por_proprietario', 'Receita por proprietário')
        ]

        for key, name in chart_info:
            count = len(charts.get(key, []))
            status = "✅" if count > 0 else "❌"
            print(f"  {status} {name}: {count} registros")

    # Data e hora do teste
    print(f"\n🕒 Teste realizado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    print("="*60)

def main():
    print("🔍 INICIANDO VERIFICAÇÃO COMPLETA DO DASHBOARD")
    print("="*60)

    # Login
    token = test_login()
    if not token:
        print("❌ Impossível continuar sem autenticação")
        return

    # Testes
    stats = test_dashboard_stats(token)
    charts = test_dashboard_charts(token)
    page_ok = test_dashboard_page()

    # Relatório final
    generate_report(stats, charts, page_ok)

    # Resumo executivo
    print("\n🎯 RESUMO EXECUTIVO:")
    tests_passed = sum([stats is not None, charts is not None, page_ok])

    if tests_passed == 3:
        print("  ✅ DASHBOARD APROVADO - Todos os sistemas funcionando")
    elif tests_passed >= 1:
        print("  ⚠️  DASHBOARD COM ALERTAS - Alguns problemas detectados")
    else:
        print("  ❌ DASHBOARD COM FALHAS - Requer atenção imediata")

if __name__ == "__main__":
    main()