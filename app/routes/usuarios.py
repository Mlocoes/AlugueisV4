from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.schemas import Usuario, UsuarioCreate, UsuarioUpdate
from app.models.usuario import Usuario as UsuarioModel
from app.core.auth import get_password_hash

router = APIRouter()

@router.get("/", response_model=List[Usuario])
def read_usuarios(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_active_user)
):
    usuarios = db.query(UsuarioModel).offset(skip).limit(limit).all()
    
    # Conversão manual para evitar problemas de tipos
    result = []
    for usuario in usuarios:
        usuario_dict = {
            'id': usuario.id,
            'username': usuario.username,
            'nome': usuario.nome,
            'sobrenome': usuario.sobrenome,
            'tipo': usuario.tipo,
            'email': usuario.email,
            'telefone': usuario.telefone,
            'documento': usuario.documento,
            'tipo_documento': usuario.tipo_documento,
            'endereco': usuario.endereco,
            'ativo': bool(usuario.ativo) if usuario.ativo is not None else True
        }
        result.append(usuario_dict)
    
    return result

@router.post("/", response_model=Usuario)
def create_usuario(
    usuario: UsuarioCreate,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_active_user)
):
    # Verificar se email já existe
    db_usuario = db.query(UsuarioModel).filter(UsuarioModel.email == usuario.email).first()
    if db_usuario:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Criar novo usuário
    # Gerar username automaticamente baseado no email
    username = usuario.email.split('@')[0].lower()
    # Verificar se username já existe e adicionar sufixo se necessário
    original_username = username
    counter = 1
    while db.query(UsuarioModel).filter(UsuarioModel.username == username).first():
        username = f"{original_username}{counter}"
        counter += 1
    
    # Usar senha padrão para proprietários (deve ser alterada depois)
    default_password = "123456"
    hashed_password = get_password_hash(default_password)
    
    db_usuario = UsuarioModel(
        username=username,
        nome=usuario.nome,
        tipo=usuario.tipo,
        email=usuario.email,
        telefone=usuario.telefone,
        hashed_password=hashed_password,
        ativo=usuario.ativo
    )
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

@router.get("/{usuario_id}", response_model=Usuario)
def read_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_active_user)
):
    db_usuario = db.query(UsuarioModel).filter(UsuarioModel.id == usuario_id).first()
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_usuario

@router.put("/{usuario_id}", response_model=Usuario)
def update_usuario(
    usuario_id: int,
    usuario_update: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_active_user)
):
    db_usuario = db.query(UsuarioModel).filter(UsuarioModel.id == usuario_id).first()
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = usuario_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_usuario, field, value)
    
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

@router.delete("/{usuario_id}")
def delete_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_active_user)
):
    db_usuario = db.query(UsuarioModel).filter(UsuarioModel.id == usuario_id).first()
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(db_usuario)
    db.commit()
    return {"message": "User deleted successfully"}