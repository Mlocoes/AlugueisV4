from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.schemas import Imovel, ImovelCreate, ImovelUpdate
from app.models.imovel import Imovel as ImovelModel
from app.models.usuario import Usuario

router = APIRouter()

@router.get("/", response_model=List[Imovel])
def read_imoveis(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    imoveis = db.query(ImovelModel).offset(skip).limit(limit).all()
    return imoveis

@router.post("/", response_model=Imovel)
def create_imovel(
    imovel: ImovelCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    db_imovel = ImovelModel(**imovel.dict())
    db.add(db_imovel)
    db.commit()
    db.refresh(db_imovel)
    return db_imovel

@router.get("/{imovel_id}", response_model=Imovel)
def read_imovel(
    imovel_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    db_imovel = db.query(ImovelModel).filter(ImovelModel.id == imovel_id).first()
    if db_imovel is None:
        raise HTTPException(status_code=404, detail="Imovel not found")
    return db_imovel

@router.put("/{imovel_id}", response_model=Imovel)
def update_imovel(
    imovel_id: int,
    imovel_update: ImovelUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    db_imovel = db.query(ImovelModel).filter(ImovelModel.id == imovel_id).first()
    if db_imovel is None:
        raise HTTPException(status_code=404, detail="Imovel not found")
    
    update_data = imovel_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_imovel, field, value)
    
    db.commit()
    db.refresh(db_imovel)
    return db_imovel

@router.delete("/{imovel_id}")
def delete_imovel(
    imovel_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    db_imovel = db.query(ImovelModel).filter(ImovelModel.id == imovel_id).first()
    if db_imovel is None:
        raise HTTPException(status_code=404, detail="Imovel not found")
    
    db.delete(db_imovel)
    db.commit()
    return {"message": "Imovel deleted successfully"}