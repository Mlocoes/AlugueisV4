from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.core.permissions import require_admin
from app.schemas import Backup, BackupCreate
from app.models.backup import Backup as BackupModel
from app.models.usuario import Usuario
import os
import shutil
from datetime import datetime

router = APIRouter()

BACKUP_DIR = "backups"
os.makedirs(BACKUP_DIR, exist_ok=True)

@router.post("/", response_model=Backup)
def create_backup(backup_data: BackupCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
    """
    Cria um novo backup do sistema.
    """
    require_admin(current_user)

    # Simular criação de backup (em produção, isso faria backup real do banco)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{backup_data.tipo}_{timestamp}.sql"
    filepath = os.path.join(BACKUP_DIR, filename)

    # Simular tamanho do arquivo (em produção, calcular tamanho real)
    file_size = 1024 * 1024  # 1MB simulado

    # Criar arquivo vazio para simular
    with open(filepath, 'w') as f:
        f.write(f"-- Backup {backup_data.tipo} criado em {datetime.now()}\n")

    # Registrar no banco
    db_backup = BackupModel(
        tipo=backup_data.tipo,
        arquivo=filepath,
        tamanho=file_size,
        descricao=backup_data.descricao
    )
    db.add(db_backup)
    db.commit()
    db.refresh(db_backup)

    return db_backup

@router.get("/history/", response_model=List[Backup])
def get_backup_history(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
    """
    Lista o histórico de backups.
    """
    require_admin(current_user)

    backups = db.query(BackupModel).offset(skip).limit(limit).all()
    return backups

@router.post("/restore/")
def restore_backup(backup_file: UploadFile = File(...), db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
    """
    Restaura um backup do sistema.
    """
    require_admin(current_user)

    # Salvar arquivo temporariamente
    temp_path = f"temp_{backup_file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(backup_file.file, buffer)

    # Em produção, aqui seria executado o script de restauração
    # Por enquanto, apenas simular
    print(f"Backup {backup_file.filename} seria restaurado")

    # Limpar arquivo temporário
    os.remove(temp_path)

    return {"message": "Backup restaurado com sucesso (simulado)"}