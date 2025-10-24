from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_active_user
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
    alugueis = db.query(AluguelModel).offset(skip).limit(limit).all()
    return alugueis

@router.post("/", response_model=Aluguel)
def create_aluguel(
    aluguel: AluguelCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
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
    resultado = AluguelService.obter_total_anual(
        db, ano, id_proprietario, id_imovel
    )
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
    
    alugueis_mensais = query.offset(skip).limit(limit).all()
    
    # Retornar diretamente sem conversão manual para testar
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
    
    db.delete(db_aluguel)
    db.commit()
    
    return {"message": "Aluguel mensal deleted successfully"}

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
    
    update_data = aluguel_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_aluguel, field, value)
    
    db.commit()
    db.refresh(db_aluguel)
    return db_aluguel