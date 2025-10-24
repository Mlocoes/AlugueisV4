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
    from sqlalchemy import func, extract
    from app.models.imovel import Imovel
    from app.models.aluguel import AluguelMensal
    from app.models.usuario import Usuario
    from datetime import datetime
    
    # Contar imóveis
    total_imoveis = db.query(Imovel).count()
    
    # Receita do mês atual (todos os aluguéis mensais são considerados recebidos)
    hoje = datetime.now()
    receita_mensal = db.query(func.sum(AluguelMensal.valor_total)).filter(
        extract('year', AluguelMensal.data_referencia) == hoje.year,
        extract('month', AluguelMensal.data_referencia) == hoje.month
    ).scalar() or 0
    
    # Aluguéis ativos (todos os registros do mês atual)
    alugueis_ativos = db.query(func.count(func.distinct(AluguelMensal.id))).filter(
        extract('year', AluguelMensal.data_referencia) == hoje.year,
        extract('month', AluguelMensal.data_referencia) == hoje.month
    ).scalar() or 0
    
    # Proprietários ativos (que têm aluguéis no mês atual)
    proprietarios_ativos = db.query(func.count(func.distinct(AluguelMensal.id_proprietario))).filter(
        extract('year', AluguelMensal.data_referencia) == hoje.year,
        extract('month', AluguelMensal.data_referencia) == hoje.month
    ).scalar() or 0
    
    # Taxa de ocupação (imóveis com aluguel / total imóveis)
    imoveis_ocupados = db.query(func.count(func.distinct(AluguelMensal.id_imovel))).filter(
        extract('year', AluguelMensal.data_referencia) == hoje.year,
        extract('month', AluguelMensal.data_referencia) == hoje.month
    ).scalar() or 0
    
    taxa_ocupacao = (imoveis_ocupados / total_imoveis * 100) if total_imoveis > 0 else 0
    
    # Total de usuários
    total_usuarios = db.query(Usuario).count()
    
    return {
        "total_imoveis": total_imoveis,
        "receita_mensal": float(receita_mensal),
        "alugueis_ativos": alugueis_ativos,
        "proprietarios_ativos": proprietarios_ativos,
        "taxa_ocupacao": round(taxa_ocupacao, 1),
        "total_usuarios": total_usuarios
    }

@router.get("/charts")
def get_dashboard_charts(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
    # Dados para gráficos do dashboard
    from app.models.imovel import Imovel
    from app.models.aluguel import AluguelMensal
    from sqlalchemy import func, extract
    from datetime import datetime, timedelta
    
    # Gráfico de receita por mês (últimos 6 meses)
    receita_por_mes = []
    hoje = datetime.now()
    
    for i in range(5, -1, -1):
        mes_referencia = hoje.replace(day=1) - timedelta(days=i*30)
        ano = mes_referencia.year
        mes = mes_referencia.month
        
        # Calcular receita total do mês
        receita_mes = db.query(func.sum(AluguelMensal.valor_total)).filter(
            extract('year', AluguelMensal.data_referencia) == ano,
            extract('month', AluguelMensal.data_referencia) == mes
        ).scalar() or 0
        
        receita_por_mes.append({
            "mes": f"{mes:02d}/{ano}",
            "receita": float(receita_mes)
        })
    
    # Gráfico de status dos imóveis
    imoveis_com_aluguel = db.query(func.count(func.distinct(AluguelMensal.id_imovel))).scalar() or 0
    total_imoveis = db.query(Imovel).count()
    imoveis_disponiveis = total_imoveis - imoveis_com_aluguel
    
    status_imoveis = [
        {"status": "Alugado", "quantidade": imoveis_com_aluguel},
        {"status": "Disponível", "quantidade": imoveis_disponiveis},
        {"status": "Manutenção", "quantidade": 0}
    ]
    
    # Gráfico de distribuição por tipo de imóvel
    tipos_imoveis = db.query(
        Imovel.tipo,
        func.count(Imovel.id).label('quantidade')
    ).group_by(Imovel.tipo).all()
    
    distribuicao_tipos = [
        {"tipo": tipo or "Não informado", "quantidade": quantidade}
        for tipo, quantidade in tipos_imoveis
    ]
    
    # Gráfico de receita por proprietário (top 5)
    receita_proprietarios = db.query(
        AluguelMensal.id_proprietario,
        func.sum(AluguelMensal.valor_proprietario).label('total_receita')
    ).group_by(AluguelMensal.id_proprietario).order_by(
        func.sum(AluguelMensal.valor_proprietario).desc()
    ).limit(5).all()
    
    receita_por_proprietario = []
    for proprietario_id, total in receita_proprietarios:
        proprietario = db.query(Usuario).filter(Usuario.id == proprietario_id).first()
        nome = proprietario.nome if proprietario else f"ID {proprietario_id}"
        receita_por_proprietario.append({
            "proprietario": nome,
            "receita": float(total)
        })
    
    return {
        "receita_por_mes": receita_por_mes,
        "status_imoveis": status_imoveis,
        "distribuicao_tipos": distribuicao_tipos,
        "receita_por_proprietario": receita_por_proprietario
    }