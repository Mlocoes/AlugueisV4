from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_active_user, get_current_admin_user
from app.core.permissions import filter_by_permissions, can_edit_financial_data
from app.schemas import Participacao, ParticipacaoCreate, ParticipacaoUpdate
from app.models.participacao import Participacao as ParticipacaoModel
from app.models.usuario import Usuario
from app.services.participacao_service import ParticipacaoService

router = APIRouter()

@router.get("/", response_model=List[Participacao])
def read_participacoes(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    # Aplicar filtros de permissão financeira
    query = db.query(ParticipacaoModel)
    query = filter_by_permissions(query, current_user, db, 'id_proprietario')
    
    participacoes = query.offset(skip).limit(limit).all()
    return participacoes

@router.post("/", response_model=Participacao)
def create_participacao(
    participacao: ParticipacaoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    # Verificar permissões para editar dados do proprietário
    if not can_edit_financial_data(current_user, participacao.id_proprietario, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para criar participações para este proprietário"
        )
    
    # Verificar se já existe participação para este imóvel e proprietário na mesma data
    existing = db.query(ParticipacaoModel).filter(
        ParticipacaoModel.id_imovel == participacao.id_imovel,
        ParticipacaoModel.id_proprietario == participacao.id_proprietario,
        ParticipacaoModel.data_cadastro == participacao.data_cadastro
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Participação já existe para esta data")
    
    # Validar soma de participações antes de criar
    ParticipacaoService.validar_antes_criar(
        db,
        participacao.id_imovel,
        participacao.participacao,
        str(participacao.data_cadastro)
    )
    
    db_participacao = ParticipacaoModel(**participacao.dict())
    db.add(db_participacao)
    db.commit()
    db.refresh(db_participacao)
    return db_participacao

@router.get("/{participacao_id}", response_model=Participacao)
def read_participacao(
    participacao_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    db_participacao = db.query(ParticipacaoModel).filter(ParticipacaoModel.id == participacao_id).first()
    if db_participacao is None:
        raise HTTPException(status_code=404, detail="Participacao not found")
    
    # Verificar se usuário tem permissão para ver esta participação (visualizar)
    from app.core.permissions import can_view_financial_data
    if not can_view_financial_data(current_user, db_participacao.id_proprietario, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para acessar esta participação"
        )
    
    return db_participacao

@router.put("/{participacao_id}", response_model=Participacao)
def update_participacao(
    participacao_id: int,
    participacao_update: ParticipacaoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    db_participacao = db.query(ParticipacaoModel).filter(ParticipacaoModel.id == participacao_id).first()
    if db_participacao is None:
        raise HTTPException(status_code=404, detail="Participacao not found")
    
    # Verificar permissões para editar dados do proprietário
    if not can_edit_financial_data(current_user, db_participacao.id_proprietario, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para editar esta participação"
        )
    
    # Se estiver atualizando a participação, validar soma
    if participacao_update.participacao is not None:
        ParticipacaoService.validar_antes_atualizar(
            db,
            participacao_id,
            db_participacao.id_imovel,
            participacao_update.participacao,
            str(db_participacao.data_cadastro)
        )
    
    update_data = participacao_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_participacao, field, value)
    
    db.commit()
    db.refresh(db_participacao)
    return db_participacao

@router.delete("/{participacao_id}")
def delete_participacao(
    participacao_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    db_participacao = db.query(ParticipacaoModel).filter(ParticipacaoModel.id == participacao_id).first()
    if db_participacao is None:
        raise HTTPException(status_code=404, detail="Participacao not found")
    
    # Verificar permissões para excluir dados do proprietário
    if not can_edit_financial_data(current_user, db_participacao.id_proprietario, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para excluir esta participação"
        )
    
    db.delete(db_participacao)
    db.commit()
    return {"message": "Participação deletada com sucesso"}

@router.get("/validar/{imovel_id}")
def validar_participacoes_imovel(
    imovel_id: int,
    data_cadastro: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Valida se a soma das participações de um imóvel está dentro da tolerância
    """
    resultado = ParticipacaoService.validar_soma_participacoes(
        db, imovel_id, data_cadastro
    )
    return resultado

@router.get("/imovel/{imovel_id}/datas")
def obter_datas_participacoes(
    imovel_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtém todas as datas de cadastro disponíveis para um imóvel
    """
    datas = ParticipacaoService.obter_datas_disponiveis(db, imovel_id)
    return {"imovel_id": imovel_id, "datas": datas}

@router.get("/imovel/{imovel_id}/lista")
def listar_participacoes_imovel(
    imovel_id: int,
    data_cadastro: str = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Lista todas as participações de um imóvel, opcionalmente filtradas por data
    """
    participacoes = ParticipacaoService.obter_participacoes_por_imovel(
        db, imovel_id, data_cadastro
    )
    return {"imovel_id": imovel_id, "participacoes": participacoes}

@router.get("/export")
def export_participacoes(
    imovel: str = None,
    proprietario: str = None,
    format: str = "excel",
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Exportar participações filtradas para Excel ou CSV
    """
    from fastapi.responses import StreamingResponse
    import io
    import pandas as pd
    from datetime import datetime
    
    # Aplicar filtros de permissão financeira
    query = db.query(ParticipacaoModel)
    query = filter_by_permissions(query, current_user, db, 'id_proprietario')
    
    # Filtro por imóvel
    if imovel:
        try:
            imovel_id = int(imovel)
            query = query.filter(ParticipacaoModel.id_imovel == imovel_id)
        except ValueError:
            pass  # Ignorar se não for um ID válido
    
    # Filtro por proprietário
    if proprietario:
        try:
            proprietario_id = int(proprietario)
            query = query.filter(ParticipacaoModel.id_proprietario == proprietario_id)
        except ValueError:
            pass  # Ignorar se não for um ID válido
    
    participacoes = query.all()
    
    # Preparar dados para exportação
    data = []
    for participacao in participacoes:
        # Buscar informações relacionadas
        imovel_info = db.query(db.query(ParticipacaoModel).filter(ParticipacaoModel.id == participacao.id).first())
        proprietario_info = db.query(Usuario).filter(Usuario.id == participacao.id_proprietario).first()
        
        # Corrigir a query do imóvel - preciso buscar da tabela imovel
        from app.models.imovel import Imovel
        imovel_info = db.query(Imovel).filter(Imovel.id == participacao.id_imovel).first()
        
        data.append({
            'ID': participacao.id,
            'Imóvel': imovel_info.endereco if imovel_info else '',
            'Proprietário': proprietario_info.nome if proprietario_info else '',
            'Percentual': float(participacao.percentual) if participacao.percentual else '',
            'Data Início': participacao.data_inicio.strftime('%d/%m/%Y') if participacao.data_inicio else '',
            'Data Fim': participacao.data_fim.strftime('%d/%m/%Y') if participacao.data_fim else '',
            'Data Cadastro': participacao.data_cadastro.strftime('%d/%m/%Y') if participacao.data_cadastro else '',
            'Ativo': 'Sim' if participacao.ativo else 'Não'
        })
    
    df = pd.DataFrame(data)
    
    # Criar buffer para o arquivo
    buffer = io.BytesIO()
    
    if format.lower() == "csv":
        # Exportar como CSV
        df.to_csv(buffer, index=False, encoding='utf-8-sig')
        buffer.seek(0)
        
        filename = f"participacoes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return StreamingResponse(
            io.BytesIO(buffer.getvalue()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    else:
        # Exportar como Excel
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Participações', index=False)
            
            # Ajustar largura das colunas
            worksheet = writer.sheets['Participações']
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
        
        filename = f"participacoes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return StreamingResponse(
            io.BytesIO(buffer.getvalue()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )