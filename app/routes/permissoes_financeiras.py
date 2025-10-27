from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.core.permissions import require_admin
from app.schemas import (
    PermissaoFinanceira,
    PermissaoFinanceiraCreate,
    PermissaoFinanceiraUpdate,
    PermissaoFinanceiraOut,
    PermissaoFinanceiraBulkCreate,
)
from app.models.permissao_financeira import PermissaoFinanceira as PermissaoFinanceiraModel
from app.models.usuario import Usuario as UsuarioModel

router = APIRouter()


@router.get("/", response_model=List[PermissaoFinanceiraOut])
def list_permissoes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: UsuarioModel = Depends(get_current_active_user)):
    """Lista permissões. Admin vê todas; usuário vê apenas permissões onde é id_usuario."""
    query = db.query(PermissaoFinanceiraModel, UsuarioModel, UsuarioModel)

    # Para evitar ambiguidades, usaremos aliases quando necessário
    # Simples approach: buscar registros e juntar nomes manualmente em memória, mas usando joins para evitar N+1
    if current_user.tipo == 'administrador':
        perms = db.query(PermissaoFinanceiraModel).offset(skip).limit(limit).all()
    else:
        perms = db.query(PermissaoFinanceiraModel).filter(PermissaoFinanceiraModel.id_usuario == current_user.id).offset(skip).limit(limit).all()

    # Pre-buscar usuários envolvidos (ids únicos) para evitar N+1
    user_ids = set()
    for p in perms:
        user_ids.add(p.id_usuario)
        user_ids.add(p.id_proprietario)

    users = {}
    if user_ids:
        rows = db.query(UsuarioModel).filter(UsuarioModel.id.in_(list(user_ids))).all()
        for u in rows:
            users[u.id] = u

    out = []
    for p in perms:
        item = PermissaoFinanceiraOut.from_orm(p)
        u = users.get(p.id_usuario)
        pr = users.get(p.id_proprietario)
        item.usuario_nome = u.nome if u else None
        item.proprietario_nome = pr.nome if pr else None
        out.append(item)

    return out


@router.get('/me', response_model=List[PermissaoFinanceiraOut])
def my_permissoes(db: Session = Depends(get_db), current_user: UsuarioModel = Depends(get_current_active_user)):
    perms = db.query(PermissaoFinanceiraModel).filter(PermissaoFinanceiraModel.id_usuario == current_user.id).all()
    user_ids = set()
    for p in perms:
        user_ids.add(p.id_usuario)
        user_ids.add(p.id_proprietario)

    users = {}
    if user_ids:
        rows = db.query(UsuarioModel).filter(UsuarioModel.id.in_(list(user_ids))).all()
        for u in rows:
            users[u.id] = u

    out = []
    for p in perms:
        item = PermissaoFinanceiraOut.from_orm(p)
        u = users.get(p.id_usuario)
        pr = users.get(p.id_proprietario)
        item.usuario_nome = u.nome if u else None
        item.proprietario_nome = pr.nome if pr else None
        out.append(item)

    return out


@router.post('/', response_model=PermissaoFinanceiraOut)
def create_permissao(permissao: PermissaoFinanceiraCreate, db: Session = Depends(get_db), current_user: UsuarioModel = Depends(get_current_active_user)):
    require_admin(current_user)

    existente = db.query(PermissaoFinanceiraModel).filter(
        PermissaoFinanceiraModel.id_usuario == permissao.id_usuario,
        PermissaoFinanceiraModel.id_proprietario == permissao.id_proprietario
    ).first()
    if existente:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Permissão já existe')

    p = PermissaoFinanceiraModel(**permissao.dict())
    db.add(p)
    db.commit()
    db.refresh(p)

    usuario = db.query(UsuarioModel).filter(UsuarioModel.id == p.id_usuario).first()
    proprietario = db.query(UsuarioModel).filter(UsuarioModel.id == p.id_proprietario).first()
    out = PermissaoFinanceiraOut.from_orm(p)
    out.usuario_nome = usuario.nome if usuario else None
    out.proprietario_nome = proprietario.nome if proprietario else None
    return out


@router.put('/{perm_id}', response_model=PermissaoFinanceiraOut)
def update_permissao(perm_id: int, data: PermissaoFinanceiraUpdate, db: Session = Depends(get_db), current_user: UsuarioModel = Depends(get_current_active_user)):
    require_admin(current_user)
    p = db.query(PermissaoFinanceiraModel).filter(PermissaoFinanceiraModel.id == perm_id).first()
    if not p:
        raise HTTPException(status_code=404, detail='Permissão não encontrada')

    update_data = data.dict(exclude_unset=True)
    for k, v in update_data.items():
        setattr(p, k, v)

    db.add(p)
    db.commit()
    db.refresh(p)

    usuario = db.query(UsuarioModel).filter(UsuarioModel.id == p.id_usuario).first()
    proprietario = db.query(UsuarioModel).filter(UsuarioModel.id == p.id_proprietario).first()
    out = PermissaoFinanceiraOut.from_orm(p)
    out.usuario_nome = usuario.nome if usuario else None
    out.proprietario_nome = proprietario.nome if proprietario else None
    return out


@router.post('/bulk', response_model=List[PermissaoFinanceiraOut])
def bulk_permissoes(payload: PermissaoFinanceiraBulkCreate, db: Session = Depends(get_db), current_user: UsuarioModel = Depends(get_current_active_user)):
    """Cria/atualiza permissões em lote em uma única transação.
    Payload: { id_usuario: int, targets: [{id_proprietario, visualizar, editar}, ...] }
    """
    require_admin(current_user)

    results = []
    # Usar transação para atomicidade
    with db.begin():
        for t in payload.targets:
            p = db.query(PermissaoFinanceiraModel).filter(
                PermissaoFinanceiraModel.id_usuario == payload.id_usuario,
                PermissaoFinanceiraModel.id_proprietario == t.id_proprietario
            ).with_for_update(nowait=False).first()

            if p:
                p.visualizar = t.visualizar
                p.editar = t.editar
                db.add(p)
            else:
                p = PermissaoFinanceiraModel(
                    id_usuario=payload.id_usuario,
                    id_proprietario=t.id_proprietario,
                    visualizar=t.visualizar,
                    editar=t.editar
                )
                db.add(p)

        # Flush to persist and allow subsequent select
        db.flush()

        # Re-fetch affected perms to return data
        proprietario_ids = [t.id_proprietario for t in payload.targets]
        perms = db.query(PermissaoFinanceiraModel).filter(
            PermissaoFinanceiraModel.id_usuario == payload.id_usuario,
            PermissaoFinanceiraModel.id_proprietario.in_(proprietario_ids)
        ).all()

    # Populate names
    user_ids = set()
    for p in perms:
        user_ids.add(p.id_usuario)
        user_ids.add(p.id_proprietario)

    users = {}
    if user_ids:
        rows = db.query(UsuarioModel).filter(UsuarioModel.id.in_(list(user_ids))).all()
        for u in rows:
            users[u.id] = u

    for p in perms:
        item = PermissaoFinanceiraOut.from_orm(p)
        item.usuario_nome = users.get(p.id_usuario).nome if users.get(p.id_usuario) else None
        item.proprietario_nome = users.get(p.id_proprietario).nome if users.get(p.id_proprietario) else None
        results.append(item)

    return results


@router.delete('/{perm_id}')
def delete_permissao(perm_id: int, db: Session = Depends(get_db), current_user: UsuarioModel = Depends(get_current_active_user)):
    require_admin(current_user)
    p = db.query(PermissaoFinanceiraModel).filter(PermissaoFinanceiraModel.id == perm_id).first()
    if not p:
        raise HTTPException(status_code=404, detail='Permissão não encontrada')
    db.delete(p)
    db.commit()
    return {'message': 'ok'}
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.core.permissions import require_admin
from app.schemas import PermissaoFinanceira, PermissaoFinanceiraCreate, PermissaoFinanceiraUpdate, PermissaoFinanceiraOut
from app.schemas import PermissaoFinanceiraBulkCreate, PermissaoTarget
from app.models.permissao_financeira import PermissaoFinanceira as PermissaoFinanceiraModel
from app.models.usuario import Usuario

router = APIRouter()


@router.get("/", response_model=List[PermissaoFinanceiraOut])
def read_permissoes_financeiras(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
    """
    Lista de todas as permissões (admin) ou permissões do próprio usuário.
    """
    # Admin vê tudo
    if current_user.tipo == 'administrador':
        records = db.query(PermissaoFinanceiraModel).offset(skip).limit(limit).all()
    else:
        # Usuário normal: retorna apenas permissões relacionadas ao próprio usuário
        records = db.query(PermissaoFinanceiraModel).filter(PermissaoFinanceiraModel.id_usuario == current_user.id).offset(skip).limit(limit).all()

    result = []
    for r in records:
        usuario = db.query(Usuario).filter(Usuario.id == r.id_usuario).first()
        proprietario = db.query(Usuario).filter(Usuario.id == r.id_proprietario).first()
        out = PermissaoFinanceiraOut.from_orm(r)
        out.usuario_nome = usuario.nome if usuario else None
        out.proprietario_nome = proprietario.nome if proprietario else None
        result.append(out)
    return result


@router.get('/me', response_model=List[PermissaoFinanceiraOut])
def read_my_permissoes(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
    """Retorna as permissões do usuário autenticado."""
    records = db.query(PermissaoFinanceiraModel).filter(PermissaoFinanceiraModel.id_usuario == current_user.id).all()
    result = []
    for r in records:
        usuario = db.query(Usuario).filter(Usuario.id == r.id_usuario).first()
        proprietario = db.query(Usuario).filter(Usuario.id == r.id_proprietario).first()
        out = PermissaoFinanceiraOut.from_orm(r)
        out.usuario_nome = usuario.nome if usuario else None
        out.proprietario_nome = proprietario.nome if proprietario else None
        result.append(out)
    return result


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

    usuario = db.query(Usuario).filter(Usuario.id == db_permissao.id_usuario).first()
    proprietario = db.query(Usuario).filter(Usuario.id == db_permissao.id_proprietario).first()
    out = PermissaoFinanceiraOut.from_orm(db_permissao)
    out.usuario_nome = usuario.nome if usuario else None
    out.proprietario_nome = proprietario.nome if proprietario else None
    return out


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

    usuario = db.query(Usuario).filter(Usuario.id == db_perm.id_usuario).first()
    proprietario = db.query(Usuario).filter(Usuario.id == db_perm.id_proprietario).first()
    out = PermissaoFinanceiraOut.from_orm(db_perm)
    out.usuario_nome = usuario.nome if usuario else None
    out.proprietario_nome = proprietario.nome if proprietario else None
    return out



@router.post('/bulk', response_model=List[PermissaoFinanceiraOut])
def bulk_create_permissoes(payload: PermissaoFinanceiraBulkCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
    """Cria ou atualiza permissões em lote para um `id_usuario` afetado.

    Apenas administradores podem executar esta operação.
    """
    require_admin(current_user)

    results = []
    for t in payload.targets:
        # Verificar se existe
        db_perm = db.query(PermissaoFinanceiraModel).filter(
            PermissaoFinanceiraModel.id_usuario == payload.id_usuario,
            PermissaoFinanceiraModel.id_proprietario == t.id_proprietario
        ).first()

        if db_perm:
            # Atualizar campos
            db_perm.visualizar = t.visualizar
            db_perm.editar = t.editar
            db.add(db_perm)
        else:
            db_perm = PermissaoFinanceiraModel(
                id_usuario=payload.id_usuario,
                id_proprietario=t.id_proprietario,
                visualizar=t.visualizar,
                editar=t.editar
            )
            db.add(db_perm)

        db.commit()
        db.refresh(db_perm)

        usuario = db.query(Usuario).filter(Usuario.id == db_perm.id_usuario).first()
        proprietario = db.query(Usuario).filter(Usuario.id == db_perm.id_proprietario).first()
        out = PermissaoFinanceiraOut.from_orm(db_perm)
        out.usuario_nome = usuario.nome if usuario else None
        out.proprietario_nome = proprietario.nome if proprietario else None
        results.append(out)

    return results


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