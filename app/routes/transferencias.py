from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.schemas import Transferencia, TransferenciaCreate, TransferenciaUpdate
from app.models.transferencia import Transferencia as TransferenciaModel
from app.models.usuario import Usuario

router = APIRouter()

@router.get("/", response_model=List[Transferencia])
def read_transferencias(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
    return db.query(TransferenciaModel).offset(skip).limit(limit).all()

@router.post("/", response_model=Transferencia)
def create_transferencia(transferencia: TransferenciaCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
    db_transferencia = TransferenciaModel(**transferencia.dict())
    db.add(db_transferencia)
    db.commit()
    db.refresh(db_transferencia)
    return db_transferencia