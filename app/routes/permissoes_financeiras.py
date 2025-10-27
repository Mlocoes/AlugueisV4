from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.core.permissions import require_admin
from app.schemas import PermissaoFinanceira, PermissaoFinanceiraCreate, PermissaoFinanceiraUpdate, PermissaoFinanceiraBulkCreate, PermissaoFinanceiraOut, PermissaoTarget
from app.models.permissao_financeira import PermissaoFinanceira as PermissaoFinanceiraModel
from app.models.usuario import Usuario

router = APIRouter()


@router.get("/", response_model=List[PermissaoFinanceiraOut])
def read_permissoes_financeiras(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
    """
    Lista de todas as permissões (admin) ou permissões do próprio usuário, enriquecidas com nomes.
    """
    # Admin vê tudo
    if current_user.tipo == 'administrador':
        perms = db.query(PermissaoFinanceiraModel).offset(skip).limit(limit).all()
    else:
        # Usuário normal: retorna apenas permissões relacionadas ao próprio usuário
        perms = db.query(PermissaoFinanceiraModel).filter(PermissaoFinanceiraModel.id_usuario == current_user.id).offset(skip).limit(limit).all()

    # Obter nomes em lote
    usuario_ids = set(p.id_usuario for p in perms)
    proprietario_ids = set(p.id_proprietario for p in perms)
    all_ids = usuario_ids | proprietario_ids
    usuarios = db.query(Usuario).filter(Usuario.id.in_(all_ids)).all()
    usuario_dict = {u.id: u.nome for u in usuarios}

    # Enriquecer
    enriched = []
    for perm in perms:
        enriched.append(PermissaoFinanceiraOut(
            id=perm.id,
            id_usuario=perm.id_usuario,
            usuario_nome=usuario_dict.get(perm.id_usuario),
            id_proprietario=perm.id_proprietario,
            proprietario_nome=usuario_dict.get(perm.id_proprietario),
            visualizar=perm.visualizar,
            editar=perm.editar,
            data_criacao=perm.data_criacao
        ))
    return enriched


@router.get('/me', response_model=List[PermissaoFinanceiraOut])
def read_my_permissoes(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
    """Retorna as permissões do usuário autenticado, enriquecidas com nomes."""
    perms = db.query(PermissaoFinanceiraModel).filter(PermissaoFinanceiraModel.id_usuario == current_user.id).all()

    # Obter nomes
    proprietario_ids = set(p.id_proprietario for p in perms)
    proprietarios = db.query(Usuario).filter(Usuario.id.in_(proprietario_ids)).all()
    prop_dict = {p.id: p.nome for p in proprietarios}

    enriched = []
    for perm in perms:
        enriched.append(PermissaoFinanceiraOut(
            id=perm.id,
            id_usuario=perm.id_usuario,
            usuario_nome=current_user.nome,
            id_proprietario=perm.id_proprietario,
            proprietario_nome=prop_dict.get(perm.id_proprietario),
            visualizar=perm.visualizar,
            editar=perm.editar,
            data_criacao=perm.data_criacao
        ))
    return enriched


@router.post("/", response_model=PermissaoFinanceiraOut)
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

    # Enriquecer
    usuario = db.query(Usuario).filter(Usuario.id == db_permissao.id_usuario).first()
    proprietario = db.query(Usuario).filter(Usuario.id == db_permissao.id_proprietario).first()
    return PermissaoFinanceiraOut(
        id=db_permissao.id,
        id_usuario=db_permissao.id_usuario,
        usuario_nome=usuario.nome if usuario else None,
        id_proprietario=db_permissao.id_proprietario,
        proprietario_nome=proprietario.nome if proprietario else None,
        visualizar=db_permissao.visualizar,
        editar=db_permissao.editar,
        data_criacao=db_permissao.data_criacao
    )


@router.put("/{perm_id}", response_model=PermissaoFinanceiraOut)
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

    # Enriquecer
    usuario = db.query(Usuario).filter(Usuario.id == db_perm.id_usuario).first()
    proprietario = db.query(Usuario).filter(Usuario.id == db_perm.id_proprietario).first()
    return PermissaoFinanceiraOut(
        id=db_perm.id,
        id_usuario=db_perm.id_usuario,
        usuario_nome=usuario.nome if usuario else None,
        id_proprietario=db_perm.id_proprietario,
        proprietario_nome=proprietario.nome if proprietario else None,
        visualizar=db_perm.visualizar,
        editar=db_perm.editar,
        data_criacao=db_perm.data_criacao
    )


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


@router.post("/bulk", response_model=List[PermissaoFinanceiraOut])
def create_bulk_permissoes_financeiras(bulk_data: PermissaoFinanceiraBulkCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
    """
    Cria ou atualiza múltiplas permissões em lote para um usuário afetado.
    """
    require_admin(current_user)

    if not bulk_data.targets:
        raise HTTPException(status_code=400, detail="Deve fornecer ao menos um target")

    # Validar se o usuário afetado existe
    usuario_afetado = db.query(Usuario).filter(Usuario.id == bulk_data.id_usuario).first()
    if not usuario_afetado:
        raise HTTPException(status_code=400, detail=f"Usuário afetado com ID {bulk_data.id_usuario} não encontrado")

    # Validar se todos os proprietários existem
    proprietario_ids = [t.id_proprietario for t in bulk_data.targets]
    proprietarios_existentes = db.query(Usuario).filter(Usuario.id.in_(proprietario_ids)).all()
    proprietarios_existentes_ids = {u.id for u in proprietarios_existentes}
    proprietarios_nao_encontrados = set(proprietario_ids) - proprietarios_existentes_ids
    if proprietarios_nao_encontrados:
        raise HTTPException(status_code=400, detail=f"Proprietários não encontrados: {list(proprietarios_nao_encontrados)}")

    created_or_updated = []
    for target in bulk_data.targets:
        # Verificar se já existe
        existente = db.query(PermissaoFinanceiraModel).filter(
            PermissaoFinanceiraModel.id_usuario == bulk_data.id_usuario,
            PermissaoFinanceiraModel.id_proprietario == target.id_proprietario
        ).first()

        if existente:
            # Atualizar
            existente.visualizar = target.visualizar
            existente.editar = target.editar
            db_perm = existente
        else:
            # Criar nova
            db_perm = PermissaoFinanceiraModel(
                id_usuario=bulk_data.id_usuario,
                id_proprietario=target.id_proprietario,
                visualizar=target.visualizar,
                editar=target.editar
            )
            db.add(db_perm)

        db.flush()  # Para obter o id se novo
        created_or_updated.append(db_perm)

    # Enriquecer com nomes
    enriched = []
    usuario_nomes = {u.id: u.nome for u in db.query(Usuario).filter(Usuario.id.in_([bulk_data.id_usuario] + [t.id_proprietario for t in bulk_data.targets])).all()}
    for perm in created_or_updated:
        enriched.append(PermissaoFinanceiraOut(
            id=perm.id,
            id_usuario=perm.id_usuario,
            usuario_nome=usuario_nomes.get(perm.id_usuario),
            id_proprietario=perm.id_proprietario,
            proprietario_nome=usuario_nomes.get(perm.id_proprietario),
            visualizar=perm.visualizar,
            editar=perm.editar,
            data_criacao=perm.data_criacao
        ))

    db.commit()  # Commit manual para garantir persistência
    return enriched