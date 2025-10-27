from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_active_user, get_current_admin_user
from app.core.permissions import filter_by_permissions, can_edit_financial_data, filter_inactive_records
from app.schemas import Aluguel, AluguelCreate, AluguelUpdate, AluguelMensal, AluguelMensalCreate, AluguelMensalUpdate
from app.models.aluguel import Aluguel as AluguelModel, AluguelMensal as AluguelMensalModel
from app.models.usuario import Usuario
from app.services.aluguel_service import AluguelService

router = APIRouter()

@router.get("/", response_model=List[Aluguel])
def read_alugueis(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    # Aplicar filtros de permissão financeira
    query = db.query(AluguelModel)
    query = filter_by_permissions(query, current_user, db, 'id_proprietario')
    
    alugueis = query.offset(skip).limit(limit).all()
    return alugueis

@router.post("/", response_model=Aluguel)
def create_aluguel(
    aluguel: AluguelCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    # Verificar permissões para editar dados do proprietário
    if not can_edit_financial_data(current_user, aluguel.id_proprietario, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para criar aluguéis para este proprietário"
        )
    
    db_aluguel = AluguelModel(**aluguel.dict())
    db.add(db_aluguel)
    db.commit()
    db.refresh(db_aluguel)
    return db_aluguel

@router.get("/{aluguel_id}", response_model=Aluguel)
def read_aluguel(
    aluguel_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    db_aluguel = db.query(AluguelModel).filter(AluguelModel.id == aluguel_id).first()
    if db_aluguel is None:
        raise HTTPException(status_code=404, detail="Aluguel not found")
    
    # Verificar se usuário tem permissão para ver este aluguel (visualizar)
    from app.core.permissions import can_view_financial_data
    if not can_view_financial_data(current_user, db_aluguel.id_proprietario, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para acessar este aluguel"
        )
    
    return db_aluguel

@router.put("/{aluguel_id}", response_model=Aluguel)
def update_aluguel(
    aluguel_id: int,
    aluguel_update: AluguelUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    db_aluguel = db.query(AluguelModel).filter(AluguelModel.id == aluguel_id).first()
    if db_aluguel is None:
        raise HTTPException(status_code=404, detail="Aluguel not found")
    
    # Verificar permissões para editar dados do proprietário
    if not can_edit_financial_data(current_user, db_aluguel.id_proprietario, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para editar este aluguel"
        )
    
    update_data = aluguel_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_aluguel, field, value)
    
    db.commit()
    db.refresh(db_aluguel)
    return db_aluguel

@router.delete("/{aluguel_id}")
def delete_aluguel(
    aluguel_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    db_aluguel = db.query(AluguelModel).filter(AluguelModel.id == aluguel_id).first()
    if db_aluguel is None:
        raise HTTPException(status_code=404, detail="Aluguel not found")
    
    # Verificar permissões para excluir dados do proprietário
    if not can_edit_financial_data(current_user, db_aluguel.id_proprietario, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para excluir este aluguel"
        )
    
    db.delete(db_aluguel)
    db.commit()
    return {"message": "Aluguel deletado com sucesso"}

# Novos endpoints para relatórios financeiros

@router.get("/relatorios/anual/{ano}")
def obter_total_anual(
    ano: int,
    id_proprietario: Optional[int] = Query(None, description="Filtrar por proprietário"),
    id_imovel: Optional[int] = Query(None, description="Filtrar por imóvel"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Calcula totais de aluguéis para um ano específico
    """
    # Aplicar filtro de permissões: se usuário não for admin, limitar por proprietários permitidos
    resultado = AluguelService.obter_total_anual(
        db, ano, id_proprietario, id_imovel
    )
    # Se o resultado vier em formato de query, o serviço deve já respeitar permissões;
    # aqui filtramos novamente por segurança caso retorne uma lista/iterable
    # NOTA: AluguelService deve ser adaptado para aceitar usuário/db quando necessário.
    return resultado

@router.get("/relatorios/mensal/{ano}/{mes}")
def obter_total_mensal(
    ano: int,
    mes: int,
    id_proprietario: Optional[int] = Query(None, description="Filtrar por proprietário"),
    id_imovel: Optional[int] = Query(None, description="Filtrar por imóvel"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Calcula totais de aluguéis para um mês específico
    """
    if mes < 1 or mes > 12:
        raise HTTPException(status_code=400, detail="Mês deve estar entre 1 e 12")
    
    resultado = AluguelService.obter_total_mensal(
        db, ano, mes, id_proprietario, id_imovel
    )
    return resultado
    return resultado

@router.get("/relatorios/por-proprietario/{ano}")
def obter_relatorio_por_proprietario(
    ano: int,
    mes: Optional[int] = Query(None, description="Filtrar por mês (1-12)"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Gera relatório de aluguéis agrupado por proprietário
    """
    if mes and (mes < 1 or mes > 12):
        raise HTTPException(status_code=400, detail="Mês deve estar entre 1 e 12")
    
    resultado = AluguelService.obter_relatorio_por_proprietario(db, ano, mes)
    # Filtrar resultados pelo conjunto de proprietários permitidos para o usuário
    from app.core.permissions import get_permitted_proprietarios
    permitted = get_permitted_proprietarios(current_user, db)
    if not current_user or current_user.tipo != 'administrador':
        # Apenas retornar dados para proprietários permitidos
        resultado = [r for r in resultado if r.get('id_proprietario') in permitted]

    return {"ano": ano, "mes": mes, "dados": resultado}

@router.get("/relatorios/por-imovel/{ano}")
def obter_relatorio_por_imovel(
    ano: int,
    mes: Optional[int] = Query(None, description="Filtrar por mês (1-12)"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Gera relatório de aluguéis agrupado por imóvel
    """
    if mes and (mes < 1 or mes > 12):
        raise HTTPException(status_code=400, detail="Mês deve estar entre 1 e 12")
    
    resultado = AluguelService.obter_relatorio_por_imovel(db, ano, mes)
    # Filtrar por permissões: se o usuário não tem acesso ao proprietário do imóvel, remover
    from app.core.permissions import get_permitted_proprietarios
    permitted = get_permitted_proprietarios(current_user, db)
    if not current_user or current_user.tipo != 'administrador':
        # Supõe que cada item em resultado tem campo 'id_proprietario'
        resultado = [r for r in resultado if r.get('id_proprietario') in permitted]

    return {"ano": ano, "mes": mes, "dados": resultado}
    return {"message": "Aluguel deleted successfully"}

# Endpoints para Aluguéis Mensais (dados importados)

@router.get("/mensais/")
def read_alugueis_mensais(
    skip: int = 0,
    limit: int = 1000,
    imovel_id: Optional[int] = None,
    proprietario_id: Optional[int] = None,
    ano: Optional[int] = None,
    mes: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    query = db.query(AluguelMensalModel)
    
    if imovel_id:
        query = query.filter(AluguelMensalModel.id_imovel == imovel_id)
    if proprietario_id:
        query = query.filter(AluguelMensalModel.id_proprietario == proprietario_id)
    if ano and mes:
        from datetime import date
        data_inicio = date(ano, mes, 1)
        if mes == 12:
            data_fim = date(ano + 1, 1, 1)
        else:
            data_fim = date(ano, mes + 1, 1)
        query = query.filter(AluguelMensalModel.data_referencia >= data_inicio, 
                           AluguelMensalModel.data_referencia < data_fim)
    
    # Aplicar filtros de permissão e visibilidade (registros inativos)
    query = filter_by_permissions(query, current_user, db, 'id_proprietario')
    query = filter_inactive_records(query, current_user, 'ativo') if hasattr(AluguelMensalModel, 'ativo') else query

    alugueis_mensais = query.offset(skip).limit(limit).all()
    return alugueis_mensais

@router.get("/mensais/{aluguel_mensal_id}", response_model=AluguelMensal)
def read_aluguel_mensal(
    aluguel_mensal_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    db_aluguel = db.query(AluguelMensalModel).filter(AluguelMensalModel.id == aluguel_mensal_id).first()
    if db_aluguel is None:
        raise HTTPException(status_code=404, detail="Aluguel mensal not found")
    # Verificar permissão para acessar este registro (visualizar)
    from app.core.permissions import can_view_financial_data
    if not can_view_financial_data(current_user, db_aluguel.id_proprietario, db):
        raise HTTPException(status_code=403, detail="Você não tem permissão para acessar este aluguel mensal")

    return db_aluguel

@router.delete("/mensais/{aluguel_mensal_id}")
def delete_aluguel_mensal(
    aluguel_mensal_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    db_aluguel = db.query(AluguelMensalModel).filter(AluguelMensalModel.id == aluguel_mensal_id).first()
    if db_aluguel is None:
        raise HTTPException(status_code=404, detail="Aluguel mensal not found")
    
    from app.core.permissions import can_edit_financial_data
    if not can_edit_financial_data(current_user, db_aluguel.id_proprietario, db):
        raise HTTPException(status_code=403, detail="Você não tem permissão para excluir este aluguel mensal")

    db.delete(db_aluguel)
    db.commit()

    return {"message": "Aluguel mensal deletado com sucesso"}

@router.put("/mensais/{aluguel_mensal_id}", response_model=AluguelMensal)
def update_aluguel_mensal(
    aluguel_mensal_id: int,
    aluguel_update: AluguelMensalUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    db_aluguel = db.query(AluguelMensalModel).filter(AluguelMensalModel.id == aluguel_mensal_id).first()
    if db_aluguel is None:
        raise HTTPException(status_code=404, detail="Aluguel mensal not found")
    
    from app.core.permissions import can_edit_financial_data
    if not can_edit_financial_data(current_user, db_aluguel.id_proprietario, db):
        raise HTTPException(status_code=403, detail="Você não tem permissão para editar este aluguel mensal")

    update_data = aluguel_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_aluguel, field, value)

    db.commit()
    db.refresh(db_aluguel)
    return db_aluguel

@router.get("/export")
def export_alugueis(
    imovel: str = None,
    status: str = None,
    mes: str = None,
    format: str = "excel",
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Exportar aluguéis filtrados para Excel ou CSV
    """
    from fastapi.responses import StreamingResponse
    import io
    import pandas as pd
    from datetime import datetime
    
    # Aplicar filtros de permissão financeira
    query = db.query(AluguelMensalModel)
    query = filter_by_permissions(query, current_user, db, 'id_proprietario')
    
    # Filtro por imóvel
    if imovel:
        try:
            imovel_id = int(imovel)
            query = query.filter(AluguelMensalModel.id_imovel == imovel_id)
        except ValueError:
            pass  # Ignorar se não for um ID válido
    
    # Filtro por status
    if status and status != "Todos":
        query = query.filter(AluguelMensalModel.status == status)
    
    # Filtro por mês de referência
    if mes:
        try:
            # Formato esperado: YYYY-MM
            ano, mes_num = mes.split('-')
            query = query.filter(
                AluguelMensalModel.ano == int(ano),
                AluguelMensalModel.mes == int(mes_num)
            )
        except ValueError:
            pass  # Ignorar se formato inválido
    
    alugueis = query.all()
    
    # Preparar dados para exportação
    data = []
    for aluguel in alugueis:
        # Buscar informações relacionadas
        imovel_info = db.query(AluguelModel).filter(AluguelModel.id == aluguel.id_aluguel).first()
        proprietario_info = None
        if imovel_info:
            proprietario_info = db.query(Usuario).filter(Usuario.id == imovel_info.id_proprietario).first()
        
        data.append({
            'ID': aluguel.id,
            'Imóvel': imovel_info.endereco if imovel_info else '',
            'Proprietário': proprietario_info.nome if proprietario_info else '',
            'Inquilino': aluguel.inquilino or '',
            'Valor': float(aluguel.valor) if aluguel.valor else '',
            'Dia Vencimento': aluguel.dia_vencimento,
            'Mês Referência': f"{aluguel.ano:04d}-{aluguel.mes:02d}",
            'Data Início': aluguel.data_inicio.strftime('%d/%m/%Y') if aluguel.data_inicio else '',
            'Data Fim': aluguel.data_fim.strftime('%d/%m/%Y') if aluguel.data_fim else '',
            'Status': aluguel.status or '',
            'Data Criação': aluguel.created_at.strftime('%d/%m/%Y %H:%M') if aluguel.created_at else ''
        })
    
    df = pd.DataFrame(data)
    
    # Criar buffer para o arquivo
    buffer = io.BytesIO()
    
    if format.lower() == "csv":
        # Exportar como CSV
        df.to_csv(buffer, index=False, encoding='utf-8-sig')
        buffer.seek(0)
        
        filename = f"alugueis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return StreamingResponse(
            io.BytesIO(buffer.getvalue()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    else:
        # Exportar como Excel
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Aluguéis', index=False)
            
            # Ajustar largura das colunas
            worksheet = writer.sheets['Aluguéis']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)  # Máximo 50 caracteres
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        buffer.seek(0)
        
        filename = f"alugueis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return StreamingResponse(
            io.BytesIO(buffer.getvalue()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )