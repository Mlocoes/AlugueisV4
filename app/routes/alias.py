from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.schemas import Alias, AliasCreate, AliasUpdate
from app.models.alias import Alias as AliasModel
from app.models.usuario import Usuario

router = APIRouter()

@router.get("/", response_model=List[Alias])
def read_aliases(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
    return db.query(AliasModel).offset(skip).limit(limit).all()

@router.post("/", response_model=Alias)
def create_alias(alias: AliasCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
    db_alias = AliasModel(**alias.dict())
    db.add(db_alias)
    db.commit()
    db.refresh(db_alias)
    return db_alias