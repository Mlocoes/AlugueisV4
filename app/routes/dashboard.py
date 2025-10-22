from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.models.usuario import Usuario

router = APIRouter()

@router.get("/")
def get_dashboard(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
    # TODO: Implementar lógica do dashboard
    return {"message": "Dashboard - Em desenvolvimento", "user": current_user.nome}

@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
    # Estatísticas básicas do dashboard
    from sqlalchemy import func
    from app.models.imovel import Imovel
    from app.models.aluguel import Aluguel
    
    # Contar imóveis
    total_imoveis = db.query(Imovel).count()
    
    # Calcular receita mensal (simplificada - soma de aluguel_liquido de todos os aluguéis)
    receita_mensal = db.query(func.sum(Aluguel.aluguel_liquido)).scalar() or 0
    
    # Contar aluguéis (total de registros)
    total_alugueis = db.query(Aluguel).count()
    
    # Aluguéis ativos (por enquanto considera todos como ativos)
    alugueis_ativos = total_alugueis
    
    # Aluguéis vencidos (simplificado - por enquanto retorna 0)
    alugueis_vencidos = 0
    
    return {
        "total_imoveis": total_imoveis,
        "receita_mensal": float(receita_mensal),
        "alugueis_ativos": alugueis_ativos,
        "alugueis_vencidos": alugueis_vencidos
    }

@router.get("/charts")
def get_dashboard_charts(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
    # Dados para gráficos do dashboard
    from app.models.imovel import Imovel
    from app.models.aluguel import Aluguel
    from sqlalchemy import func
    
    # Gráfico de receita por mês (últimos 6 meses) - dados mock por enquanto
    receita_por_mes = []
    for i in range(5, -1, -1):
        receita_por_mes.append({
            "mes": f"Mês {6-i}",
            "receita": 10000 + (i * 1000)
        })
    
    # Gráfico de status dos imóveis
    # Contar imóveis alugados (que têm aluguel ativo)
    imoveis_alugados = db.query(Imovel).join(Aluguel, Imovel.id == Aluguel.id_imovel).count()
    
    # Contar imóveis disponíveis (sem aluguel)
    imoveis_disponiveis = db.query(Imovel).outerjoin(Aluguel, Imovel.id == Aluguel.id_imovel).filter(Aluguel.id.is_(None)).count()
    
    status_imoveis = [
        {"status": "Alugado", "quantidade": imoveis_alugados},
        {"status": "Disponível", "quantidade": imoveis_disponiveis},
        {"status": "Manutenção", "quantidade": 0}
    ]
    
    return {
        "receita_por_mes": receita_por_mes,
        "status_imoveis": status_imoveis
    }