from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_active_user
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
    participacoes = db.query(ParticipacaoModel).offset(skip).limit(limit).all()
    return participacoes

@router.post("/", response_model=Participacao)
def create_participacao(
    participacao: ParticipacaoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
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