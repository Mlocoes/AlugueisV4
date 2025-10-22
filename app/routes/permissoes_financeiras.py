from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.schemas import PermissaoFinanceira, PermissaoFinanceiraCreate, PermissaoFinanceiraUpdate
from app.models.permissao_financeira import PermissaoFinanceira as PermissaoFinanceiraModel
from app.models.usuario import Usuario

router = APIRouter()

@router.get("/", response_model=List[PermissaoFinanceira])
def read_permissoes_financeiras(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
    return db.query(PermissaoFinanceiraModel).offset(skip).limit(limit).all()

@router.post("/", response_model=PermissaoFinanceira)
def create_permissao_financeira(permissao: PermissaoFinanceiraCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
    db_permissao = PermissaoFinanceiraModel(**permissao.dict())
    db.add(db_permissao)
    db.commit()
    db.refresh(db_permissao)
    return db_permissao