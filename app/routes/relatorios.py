from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_, or_, exists
from typing import Optional, List
from datetime import datetime, date
from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.models.usuario import Usuario
from app.models.imovel import Imovel
from app.models.aluguel import AluguelMensal
from app.models.participacao import Participacao
from app.models.alias import Alias
from app.models.alias_proprietario import AliasProprietario
from app.core.permissions import get_permitted_proprietarios

router = APIRouter()

@router.get("/receitas-periodo")
def get_receitas_por_periodo(
    data_inicio: date = Query(..., description="Data inicial do período"),
    data_fim: date = Query(..., description="Data final do período"),
    id_proprietario: Optional[int] = Query(None, description="ID do proprietário (opcional)"),
    id_imovel: Optional[int] = Query(None, description="ID do imóvel (opcional)"),
    id_alias: Optional[int] = Query(None, description="ID do alias (opcional)"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Relatório de receitas por período com filtros avançados
    """
    # Base query
    query = db.query(
        AluguelMensal.data_referencia,
        func.sum(AluguelMensal.valor_total).label('total_receitas'),
        func.count(func.distinct(AluguelMensal.id_imovel)).label('imoveis_ativos'),
        func.count(func.distinct(AluguelMensal.id_proprietario)).label('proprietarios_ativos')
    ).filter(
        AluguelMensal.data_referencia.between(data_inicio, data_fim)
    )

    # Aplicar filtros
    if id_proprietario:
        query = query.filter(AluguelMensal.id_proprietario == id_proprietario)

    if id_imovel:
        query = query.filter(AluguelMensal.id_imovel == id_imovel)

    if id_alias:
        # Buscar proprietários do alias
        proprietarios_alias = db.query(AliasProprietario.id_proprietario).filter(
            AliasProprietario.id_alias == id_alias
        ).subquery()
        query = query.filter(AluguelMensal.id_proprietario.in_(proprietarios_alias))

    # Agrupar por mês/ano
    query = query.group_by(
        extract('year', AluguelMensal.data_referencia),
        extract('month', AluguelMensal.data_referencia)
    ).order_by(
        extract('year', AluguelMensal.data_referencia),
        extract('month', AluguelMensal.data_referencia)
    )

    # Aplicar filtro de permissões: usuários comuns só veem proprietários permitidos (nível DB)
    if current_user.tipo != 'administrador':
        permitted = get_permitted_proprietarios(current_user, db)
        if not permitted:
            return {
                "filtros": {
                    "data_inicio": data_inicio.isoformat(),
                    "data_fim": data_fim.isoformat(),
                    "id_proprietario": id_proprietario,
                    "id_imovel": id_imovel,
                    "id_alias": id_alias
                },
                "dados": [],
                "total_geral": 0
            }

        # Se o cliente solicitou um proprietário específico, garantir que tem permissão
        if id_proprietario:
            if id_proprietario not in permitted:
                return {
                    "filtros": {
                        "data_inicio": data_inicio.isoformat(),
                        "data_fim": data_fim.isoformat(),
                        "id_proprietario": id_proprietario,
                        "id_imovel": id_imovel,
                        "id_alias": id_alias
                    },
                    "dados": [],
                    "total_geral": 0
                }
        else:
            query = query.filter(AluguelMensal.id_proprietario.in_(permitted))

    resultados = query.all()

    # Formatar resposta
    dados = []
    for row in resultados:
        dados.append({
            "periodo": row.data_referencia.strftime("%Y-%m"),
            "total_receitas": float(row.total_receitas or 0),
            "imoveis_ativos": row.imoveis_ativos,
            "proprietarios_ativos": row.proprietarios_ativos
        })

    return {
        "filtros": {
            "data_inicio": data_inicio.isoformat(),
            "data_fim": data_fim.isoformat(),
            "id_proprietario": id_proprietario,
            "id_imovel": id_imovel,
            "id_alias": id_alias
        },
        "dados": dados,
        "total_geral": sum(d["total_receitas"] for d in dados)
    }

@router.get("/receitas-proprietario")
def get_receitas_por_proprietario(
    data_inicio: date = Query(..., description="Data inicial do período"),
    data_fim: date = Query(..., description="Data final do período"),
    id_alias: Optional[int] = Query(None, description="ID do alias (opcional)"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Relatório de receitas por proprietário
    """
    # Base query com join para nome do proprietário
    query = db.query(
        Usuario.id,
        Usuario.nome,
        Usuario.sobrenome,
        func.sum(AluguelMensal.valor_proprietario).label('total_receitas'),
        func.count(func.distinct(AluguelMensal.id_imovel)).label('imoveis'),
        func.avg(AluguelMensal.taxa_administracao).label('taxa_media')
    ).join(
        AluguelMensal, Usuario.id == AluguelMensal.id_proprietario
    ).filter(
        AluguelMensal.data_referencia.between(data_inicio, data_fim)
    )

    # Filtro por alias
    if id_alias:
        proprietarios_alias = db.query(AliasProprietario.id_proprietario).filter(
            AliasProprietario.id_alias == id_alias
        ).subquery()
        query = query.filter(Usuario.id.in_(proprietarios_alias))

    # Agrupar por proprietário
    query = query.group_by(Usuario.id, Usuario.nome, Usuario.sobrenome).order_by(
        func.sum(AluguelMensal.valor_proprietario).desc()
    )

    # Aplicar filtro de permissões a nível de DB para proprietários
    if current_user.tipo != 'administrador':
        permitted = get_permitted_proprietarios(current_user, db)
        if not permitted:
            return {
                "filtros": {
                    "data_inicio": data_inicio.isoformat(),
                    "data_fim": data_fim.isoformat(),
                    "id_alias": id_alias
                },
                "dados": [],
                "total_geral": 0
            }

        query = query.filter(Usuario.id.in_(permitted))

    resultados = query.all()

    dados = []
    for row in resultados:
        dados.append({
            "id_proprietario": row.id,
            "nome": f"{row.nome} {row.sobrenome or ''}".strip(),
            "total_receitas": float(row.total_receitas or 0),
            "imoveis": row.imoveis,
            "taxa_media": float(row.taxa_media or 0)
        })

    return {
        "filtros": {
            "data_inicio": data_inicio.isoformat(),
            "data_fim": data_fim.isoformat(),
            "id_alias": id_alias
        },
        "dados": dados,
        "total_geral": sum(d["total_receitas"] for d in dados)
    }

@router.get("/performance-imoveis")
def get_performance_imoveis(
    data_inicio: date = Query(..., description="Data inicial do período"),
    data_fim: date = Query(..., description="Data final do período"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Relatório de performance dos imóveis
    """
    query = db.query(
        Imovel.id,
        Imovel.nome,
        Imovel.endereco,
        Imovel.tipo,
        func.sum(AluguelMensal.valor_total).label('receita_total'),
        func.count(AluguelMensal.id).label('meses_alugado'),
        func.avg(AluguelMensal.valor_total).label('receita_media_mensal')
    ).join(
        AluguelMensal, Imovel.id == AluguelMensal.id_imovel
    ).filter(
        AluguelMensal.data_referencia.between(data_inicio, data_fim)
    ).group_by(
        Imovel.id, Imovel.nome, Imovel.endereco, Imovel.tipo
    ).order_by(
        func.sum(AluguelMensal.valor_total).desc()
    )

    # Aplicar filtro de permissões a nível de DB para evitar N+1
    if current_user.tipo != 'administrador':
        permitted = get_permitted_proprietarios(current_user, db)
        if not permitted:
            # Sem permissões, retornar vazio
            return {"filtros": {"data_inicio": data_inicio.isoformat(), "data_fim": data_fim.isoformat()}, "dados": []}

        # Subquery EXISTS: verificar que exista um aluguel mensal para o imóvel e um proprietario permitido
        subq = db.query(AluguelMensal.id).filter(
            AluguelMensal.id_imovel == Imovel.id,
            AluguelMensal.id_proprietario.in_(permitted),
            AluguelMensal.data_referencia.between(data_inicio, data_fim)
        ).exists()

        query = query.filter(subq)

    resultados = query.all()

    dados = []
    for row in resultados:
        dados.append({
            "id_imovel": row.id,
            "nome": row.nome,
            "endereco": row.endereco,
            "tipo": row.tipo,
            "receita_total": float(row.receita_total or 0),
            "meses_alugado": row.meses_alugado,
            "receita_media_mensal": float(row.receita_media_mensal or 0)
        })

    return {
        "filtros": {
            "data_inicio": data_inicio.isoformat(),
            "data_fim": data_fim.isoformat()
        },
        "dados": dados
    }

@router.get("/alugueis-ativos")
def get_alugueis_ativos(
    mes: Optional[int] = Query(None, description="Mês (1-12)"),
    ano: Optional[int] = Query(None, description="Ano"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Relatório de aluguéis ativos
    """
    hoje = datetime.now()
    if not ano:
        ano = hoje.year
    if not mes:
        mes = hoje.month

    query = db.query(
        AluguelMensal,
        Imovel.nome.label('nome_imovel'),
        Usuario.nome.label('nome_proprietario'),
        Usuario.sobrenome.label('sobrenome_proprietario')
    ).join(
        Imovel, AluguelMensal.id_imovel == Imovel.id
    ).join(
        Usuario, AluguelMensal.id_proprietario == Usuario.id
    ).filter(
        extract('year', AluguelMensal.data_referencia) == ano,
        extract('month', AluguelMensal.data_referencia) == mes
    ).order_by(AluguelMensal.valor_total.desc())

    # Aplicar filtro de permissões (DB-level) para aluguéis ativos
    if current_user.tipo != 'administrador':
        permitted = get_permitted_proprietarios(current_user, db)
        if not permitted:
            return {
                "filtros": {
                    "mes": mes,
                    "ano": ano
                },
                "dados": [],
                "total_alugueis": 0,
                "receita_total": 0
            }

        query = query.filter(AluguelMensal.id_proprietario.in_(permitted))

    resultados = query.all()

    dados = []
    for row in resultados:
        aluguel = row[0]
        dados.append({
            "id": aluguel.id,
            "imovel": row.nome_imovel,
            "proprietario": f"{row.nome_proprietario} {row.sobrenome_proprietario or ''}".strip(),
            "valor_total": float(aluguel.valor_total),
            "valor_proprietario": float(aluguel.valor_proprietario),
            "taxa_administracao": float(aluguel.taxa_administracao or 0),
            "data_referencia": aluguel.data_referencia.isoformat()
        })

    return {
        "filtros": {
            "mes": mes,
            "ano": ano
        },
        "dados": dados,
        "total_alugueis": len(dados),
        "receita_total": sum(d["valor_total"] for d in dados)
    }

@router.get("/receitas-periodo/export/excel")
def export_receitas_periodo_excel(
    data_inicio: date = Query(..., description="Data inicial do período"),
    data_fim: date = Query(..., description="Data final do período"),
    id_proprietario: Optional[int] = Query(None, description="ID do proprietário (opcional)"),
    id_imovel: Optional[int] = Query(None, description="ID do imóvel (opcional)"),
    id_alias: Optional[int] = Query(None, description="ID do alias (opcional)"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Exportar relatório de receitas por período para Excel
    """
    # Reutilizar a lógica do endpoint normal
    data = get_receitas_por_periodo(data_inicio, data_fim, id_proprietario, id_imovel, id_alias, db, current_user)
    
    # Criar DataFrame pandas
    import pandas as pd
    from io import BytesIO
    from fastapi.responses import StreamingResponse
    
    # Garantir que os dados exportados respeitam permissões
    if current_user.tipo != 'administrador':
        permitted = get_permitted_proprietarios(current_user, db)
        data["dados"] = [d for d in data["dados"] if d.get('id_proprietario') in permitted]

    df = pd.DataFrame(data["dados"])
    df['total_receitas'] = df['total_receitas'].apply(lambda x: f"R$ {x:,.2f}")
    
    # Criar buffer
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Receitas_Periodo', index=False)
    
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={"Content-Disposition": "attachment; filename=receitas_periodo.xlsx"}
    )