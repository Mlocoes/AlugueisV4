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
    
    # Contar imóveis (este número não depende de permissões financeiras)
    total_imoveis = db.query(Imovel).count()

    # Permissões: limitar métricas financeiras aos proprietários permitidos
    permitted = None
    if current_user.tipo != 'administrador':
        from app.core.permissions import get_permitted_proprietarios
        permitted = get_permitted_proprietarios(current_user, db)
    
    # Receita do mês atual (soma única dos valores totais por imóvel)
    hoje = datetime.now()
    
    # Subquery para obter valor_total único por imóvel no mês
    # Usar uma lógica mais robusta: pegar o valor mais recente ou o maior valor positivo
    subquery_q = db.query(
        AluguelMensal.id_imovel,
        func.max(AluguelMensal.valor_total).label('valor_total_unico')
    ).filter(
        extract('year', AluguelMensal.data_referencia) == hoje.year,
        extract('month', AluguelMensal.data_referencia) == hoje.month
    )

    if permitted is not None:
        if not permitted:
            receita_mensal = 0
        else:
            subquery_q = subquery_q.filter(AluguelMensal.id_proprietario.in_(permitted))
            subquery = subquery_q.group_by(AluguelMensal.id_imovel).subquery()
            receita_mensal = db.query(func.sum(subquery.c.valor_total_unico)).scalar() or 0
    else:
        subquery = subquery_q.group_by(AluguelMensal.id_imovel).subquery()
        receita_mensal = db.query(func.sum(subquery.c.valor_total_unico)).scalar() or 0
    
    receita_mensal = db.query(func.sum(subquery.c.valor_total_unico)).scalar() or 0
    
    # Aluguéis ativos (todos os registros do mês atual)
    alugueis_ativos_q = db.query(func.count(func.distinct(AluguelMensal.id))).filter(
        extract('year', AluguelMensal.data_referencia) == hoje.year,
        extract('month', AluguelMensal.data_referencia) == hoje.month
    )
    if permitted is not None:
        if not permitted:
            alugueis_ativos = 0
        else:
            alugueis_ativos = alugueis_ativos_q.filter(AluguelMensal.id_proprietario.in_(permitted)).scalar() or 0
    else:
        alugueis_ativos = alugueis_ativos_q.scalar() or 0
    
    # Proprietários ativos (que têm aluguéis no mês atual)
    proprietarios_ativos_q = db.query(func.count(func.distinct(AluguelMensal.id_proprietario))).filter(
        extract('year', AluguelMensal.data_referencia) == hoje.year,
        extract('month', AluguelMensal.data_referencia) == hoje.month
    )
    if permitted is not None:
        if not permitted:
            proprietarios_ativos = 0
        else:
            proprietarios_ativos = proprietarios_ativos_q.filter(AluguelMensal.id_proprietario.in_(permitted)).scalar() or 0
    else:
        proprietarios_ativos = proprietarios_ativos_q.scalar() or 0
    
    # Taxa de ocupação (imóveis com aluguel / total imóveis)
    imoveis_ocupados_q = db.query(func.count(func.distinct(AluguelMensal.id_imovel))).filter(
        extract('year', AluguelMensal.data_referencia) == hoje.year,
        extract('month', AluguelMensal.data_referencia) == hoje.month
    )
    if permitted is not None:
        if not permitted:
            imoveis_ocupados = 0
        else:
            imoveis_ocupados = imoveis_ocupados_q.filter(AluguelMensal.id_proprietario.in_(permitted)).scalar() or 0
    else:
        imoveis_ocupados = imoveis_ocupados_q.scalar() or 0
    
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
    # Verificar permissões de acesso aos proprietários
    permitted = None
    if current_user.tipo != 'administrador':
        from app.core.permissions import get_permitted_proprietarios
        permitted = get_permitted_proprietarios(current_user, db)
    
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
        
        # Calcular receita total do mês (valores únicos por imóvel)
        subquery_mes = db.query(
            AluguelMensal.id_imovel,
            func.max(AluguelMensal.valor_total).label('valor_total_unico')
        ).filter(
            extract('year', AluguelMensal.data_referencia) == ano,
            extract('month', AluguelMensal.data_referencia) == mes
            # Removido filtro de valores positivos para incluir todos os valores na receita total
        ).group_by(AluguelMensal.id_imovel).subquery()
        
        receita_mes = db.query(func.sum(subquery_mes.c.valor_total_unico)).scalar() or 0
        
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
    receita_proprietarios_q = db.query(
        AluguelMensal.id_proprietario,
        func.sum(AluguelMensal.valor_proprietario).label('total_receita')
    ).group_by(AluguelMensal.id_proprietario).order_by(
        func.sum(AluguelMensal.valor_proprietario).desc()
    ).limit(5)

    if permitted is not None:
        if permitted:
            receita_proprietarios_q = receita_proprietarios_q.filter(AluguelMensal.id_proprietario.in_(permitted))
        else:
            receita_proprietarios_q = receita_proprietarios_q.filter(False)

    receita_proprietarios = receita_proprietarios_q.all()
    
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