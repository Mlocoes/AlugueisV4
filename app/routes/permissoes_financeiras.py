from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.core.permissions import require_admin
from app.schemas import PermissaoFinanceira, PermissaoFinanceiraCreate, PermissaoFinanceiraUpdate
from app.models.permissao_financeira import PermissaoFinanceira as PermissaoFinanceiraModel
from app.models.usuario import Usuario

router = APIRouter()


@router.get("/", response_model=List[PermissaoFinanceira])
def read_permissoes_financeiras(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
    """
    Lista de todas as permissões (admin) ou permissões do próprio usuário.
    """
    # Admin vê tudo
    if current_user.tipo == 'administrador':
        return db.query(PermissaoFinanceiraModel).offset(skip).limit(limit).all()

    # Usuário normal: retorna apenas permissões relacionadas ao próprio usuário
    return db.query(PermissaoFinanceiraModel).filter(PermissaoFinanceiraModel.id_usuario == current_user.id).offset(skip).limit(limit).all()


@router.get('/me', response_model=List[PermissaoFinanceira])
def read_my_permissoes(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
    """Retorna as permissões do usuário autenticado."""
    return db.query(PermissaoFinanceiraModel).filter(PermissaoFinanceiraModel.id_usuario == current_user.id).all()


@router.post("/", response_model=PermissaoFinanceira)
def create_permissao_financeira(permissao: PermissaoFinanceiraCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
    # Apenas administradores podem criar permissões
    require_admin(current_user)

    # Evitar duplicatas (unique constraint também existe)
    existente = db.query(PermissaoFinanceiraModel).filter(
        PermissaoFinanceiraModel.id_usuario == permissao.id_usuario,
        PermissaoFinanceiraModel.id_proprietario == permissao.id_proprietario
    ).first()
    if existente:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Permissão já existe para este usuário/proprietário")

    db_permissao = PermissaoFinanceiraModel(**permissao.dict())
    db.add(db_permissao)
    db.commit()
    db.refresh(db_permissao)
    return db_permissao


@router.put("/{perm_id}", response_model=PermissaoFinanceira)
def update_permissao_financeira(perm_id: int, permissao: PermissaoFinanceiraUpdate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
    # Apenas administradores podem modificar permissões
    require_admin(current_user)

    db_perm = db.query(PermissaoFinanceiraModel).filter(PermissaoFinanceiraModel.id == perm_id).first()
    if not db_perm:
        raise HTTPException(status_code=404, detail="Permissão não encontrada")

    update_data = permissao.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_perm, field, value)

    db.commit()
    db.refresh(db_perm)
    return db_perm


@router.delete("/{perm_id}")
def delete_permissao_financeira(perm_id: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
    # Apenas administradores podem deletar permissões
    require_admin(current_user)

    db_perm = db.query(PermissaoFinanceiraModel).filter(PermissaoFinanceiraModel.id == perm_id).first()
    if not db_perm:
        raise HTTPException(status_code=404, detail="Permissão não encontrada")

    db.delete(db_perm)
    db.commit()
    return {"message": "Permissão deletada com sucesso"}