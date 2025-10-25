"""
Módulo de controle de acesso e permissões
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.usuario import Usuario
from app.models.permissao_financeira import PermissaoFinanceira
from typing import List, Optional


def require_admin(current_user: Usuario) -> Usuario:
    """
    Verifica se o usuário é administrador.
    Lança HTTPException se não for admin.
    """
    if current_user.tipo != 'administrador':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem realizar esta operação"
        )
    return current_user


def is_admin(user: Usuario) -> bool:
    """Verifica se o usuário é administrador"""
    return user.tipo == 'administrador'


def get_permitted_proprietarios(user: Usuario, db: Session) -> List[int]:
    """
    Retorna lista de IDs de proprietários que o usuário pode acessar.
    - Admin: todos os proprietários
    - Usuário comum: apenas proprietários definidos em permissoes_financeiras
    """
    if is_admin(user):
        # Admin pode ver todos os proprietários
        from app.models.usuario import Usuario as UsuarioModel
        proprietarios = db.query(UsuarioModel.id).filter(
            UsuarioModel.tipo == 'usuario',  # Considerando que proprietários são usuários do tipo 'usuario'
            UsuarioModel.ativo == True
        ).all()
        return [p[0] for p in proprietarios]

    # Usuário comum: apenas proprietários com permissão
    permissoes = db.query(PermissaoFinanceira).filter(
        PermissaoFinanceira.id_usuario == user.id,
        PermissaoFinanceira.visualizar == True
    ).all()

    return [p.id_proprietario for p in permissoes]


def filter_by_permissions(query, user: Usuario, db: Session, proprietario_field: str = None):
    """
    Aplica filtros de permissão na query.

    Args:
        query: Query SQLAlchemy
        user: Usuário atual
        db: Sessão do banco
        proprietario_field: Nome do campo que referencia proprietário (opcional)

    Returns:
        Query filtrada
    """
    if is_admin(user):
        # Admin vê tudo (exceto dados inativos se especificado)
        return query

    # Usuário comum: filtrar por permissões
    permitted_proprietarios = get_permitted_proprietarios(user, db)

    if proprietario_field and permitted_proprietarios:
        # Filtrar por campo de proprietário específico
        return query.filter(getattr(query.column_descriptions[0]['entity'], proprietario_field).in_(permitted_proprietarios))
    elif permitted_proprietarios:
        # Para queries que não têm campo específico, assumir que é uma query de proprietários
        return query.filter(query.column_descriptions[0]['entity'].id.in_(permitted_proprietarios))

    # Se não há permissões, retornar query vazia
    return query.filter(False)


def can_edit_financial_data(user: Usuario, proprietario_id: int, db: Session) -> bool:
    """
    Verifica se o usuário pode editar dados financeiros de um proprietário específico.
    """
    if is_admin(user):
        return True

    # Verificar permissão específica
    permissao = db.query(PermissaoFinanceira).filter(
        PermissaoFinanceira.id_usuario == user.id,
        PermissaoFinanceira.id_proprietario == proprietario_id,
        PermissaoFinanceira.editar == True
    ).first()

    return permissao is not None


def filter_inactive_records(query, user: Usuario, active_field: str = 'ativo'):
    """
    Filtra registros inativos para usuários comuns.
    Admin vê tudo.
    """
    if is_admin(user):
        return query

    # Usuários comuns só veem registros ativos
    return query.filter(getattr(query.column_descriptions[0]['entity'], active_field) == True)