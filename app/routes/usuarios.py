from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_active_user, get_current_admin_user
from app.core.permissions import filter_inactive_records
from app.schemas import Usuario, UsuarioCreate, UsuarioUpdate
from app.models.usuario import Usuario as UsuarioModel
from app.core.auth import get_password_hash

router = APIRouter()

@router.get("/")
def read_usuarios(
    skip: int = 0,
    limit: int = 100,
    q: str = None,
    tipo: str = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)  # Só admin pode listar usuários
):
    # Aplicar filtros de permissão
    query = db.query(UsuarioModel)
    query = filter_inactive_records(query, current_user)
    
    # Filtro por tipo se especificado
    if tipo:
        query = query.filter(UsuarioModel.tipo == tipo)
    
    # Filtro por busca (nome, email, username)
    if q:
        search_term = f"%{q}%"
        query = query.filter(
            (UsuarioModel.nome.ilike(search_term)) |
            (UsuarioModel.email.ilike(search_term)) |
            (UsuarioModel.username.ilike(search_term))
        )
    
    usuarios = query.offset(skip).limit(limit).all()
    
    # Conversão manual para evitar problemas de tipos
    result = []
    for usuario in usuarios:
        usuario_dict = {
            'id': usuario.id,
            'username': usuario.username or '',
            'nome': usuario.nome or '',
            'sobrenome': usuario.sobrenome or '',
            'tipo': usuario.tipo or 'usuario',
            'email': usuario.email or '',
            'telefone': usuario.telefone or '',
            'documento': usuario.documento or '',
            'tipo_documento': usuario.tipo_documento or 'CPF',
            'endereco': usuario.endereco or '',
            'ativo': bool(usuario.ativo) if usuario.ativo is not None else True
        }
        result.append(usuario_dict)
    
    return result

@router.post("/")
def create_usuario(
    usuario: UsuarioCreate,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_admin_user)
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
    
    # Conversão manual para evitar problemas de tipos
    return {
        'id': db_usuario.id,
        'username': db_usuario.username,
        'nome': db_usuario.nome,
        'sobrenome': db_usuario.sobrenome,
        'tipo': db_usuario.tipo,
        'email': db_usuario.email,
        'telefone': db_usuario.telefone,
        'documento': db_usuario.documento,
        'tipo_documento': db_usuario.tipo_documento,
        'endereco': db_usuario.endereco,
        'ativo': bool(db_usuario.ativo) if db_usuario.ativo is not None else True
    }

@router.get("/{usuario_id}")
def read_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    db_usuario = db.query(UsuarioModel).filter(UsuarioModel.id == usuario_id).first()
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Conversão manual para evitar problemas de tipos
    return {
        'id': db_usuario.id,
        'username': db_usuario.username,
        'nome': db_usuario.nome,
        'sobrenome': db_usuario.sobrenome,
        'tipo': db_usuario.tipo,
        'email': db_usuario.email,
        'telefone': db_usuario.telefone,
        'documento': db_usuario.documento,
        'tipo_documento': db_usuario.tipo_documento,
        'endereco': db_usuario.endereco,
        'ativo': bool(db_usuario.ativo) if db_usuario.ativo is not None else True
    }

@router.put("/{usuario_id}")
def update_usuario(
    usuario_id: int,
    usuario_update: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_admin_user)
):
    db_usuario = db.query(UsuarioModel).filter(UsuarioModel.id == usuario_id).first()
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = usuario_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_usuario, field, value)
    
    db.commit()
    db.refresh(db_usuario)
    
    # Conversão manual para evitar problemas de tipos
    return {
        'id': db_usuario.id,
        'username': db_usuario.username,
        'nome': db_usuario.nome,
        'sobrenome': db_usuario.sobrenome,
        'tipo': db_usuario.tipo,
        'email': db_usuario.email,
        'telefone': db_usuario.telefone,
        'documento': db_usuario.documento,
        'tipo_documento': db_usuario.tipo_documento,
        'endereco': db_usuario.endereco,
        'ativo': bool(db_usuario.ativo) if db_usuario.ativo is not None else True
    }

@router.delete("/{usuario_id}")
def delete_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_admin_user)
):
    db_usuario = db.query(UsuarioModel).filter(UsuarioModel.id == usuario_id).first()
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(db_usuario)
    db.commit()
    return {"message": "User deleted successfully"}

@router.get("/export")
def export_usuarios(
    q: str = None,
    tipo: str = None,
    status: str = None,
    format: str = "excel",
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_admin_user)
):
    """
    Exportar usuários/proprietários filtrados para Excel ou CSV
    """
    from fastapi.responses import StreamingResponse
    import io
    import pandas as pd
    from datetime import datetime
    
    # Aplicar filtros de permissão
    query = db.query(UsuarioModel)
    query = filter_inactive_records(query, current_user)
    
    # Filtro por tipo se especificado
    if tipo and tipo != "Todos":
        query = query.filter(UsuarioModel.tipo == tipo)
    
    # Filtro por status
    if status and status != "Todos":
        if status == "Ativo":
            query = query.filter(UsuarioModel.ativo == True)
        elif status == "Inativo":
            query = query.filter(UsuarioModel.ativo == False)
    
    # Filtro por busca (nome, email, username)
    if q:
        search_term = f"%{q}%"
        query = query.filter(
            (UsuarioModel.nome.ilike(search_term)) |
            (UsuarioModel.email.ilike(search_term)) |
            (UsuarioModel.username.ilike(search_term))
        )
    
    usuarios = query.all()
    
    # Preparar dados para exportação
    data = []
    for usuario in usuarios:
        data.append({
            'ID': usuario.id,
            'Username': usuario.username or '',
            'Nome': usuario.nome or '',
            'Sobrenome': usuario.sobrenome or '',
            'Email': usuario.email or '',
            'Telefone': usuario.telefone or '',
            'CPF/CNPJ': usuario.cpf_cnpj or '',
            'Tipo': usuario.tipo or 'usuario',
            'Status': 'Ativo' if usuario.ativo else 'Inativo',
            'Data Criação': usuario.created_at.strftime('%d/%m/%Y %H:%M') if usuario.created_at else ''
        })
    
    df = pd.DataFrame(data)
    
    # Criar buffer para o arquivo
    buffer = io.BytesIO()
    
    if format.lower() == "csv":
        # Exportar como CSV
        df.to_csv(buffer, index=False, encoding='utf-8-sig')
        buffer.seek(0)
        
        filename = f"usuarios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return StreamingResponse(
            io.BytesIO(buffer.getvalue()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    else:
        # Exportar como Excel
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Usuários', index=False)
            
            # Ajustar largura das colunas
            worksheet = writer.sheets['Usuários']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)  # Máximo 50 caracteres
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        buffer.seek(0)
        
        filename = f"usuarios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return StreamingResponse(
            io.BytesIO(buffer.getvalue()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )