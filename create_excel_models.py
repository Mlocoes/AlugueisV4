"""DEPRECATED: movido para scripts/create_excel_models.py

Shim que executa as funções que criam os modelos Excel no novo local.
"""
from scripts.create_excel_models import (
    create_proprietarios_model,
    create_imoveis_model,
    create_participacoes_model,
    create_alugueis_model,
)


if __name__ == "__main__":
    print("\n🔨 Criando arquivos modelo Excel...\n")
    create_proprietarios_model()
    create_imoveis_model()
    create_participacoes_model()
    create_alugueis_model()
    print("\n✅ Modelos criados em scripts/create_excel_models.py")
