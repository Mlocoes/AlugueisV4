from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.schemas import Imovel, ImovelCreate, ImovelUpdate
from app.models.imovel import Imovel as ImovelModel
from app.models.usuario import Usuario

router = APIRouter()

@router.get("/")
def read_imoveis(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    imoveis = db.query(ImovelModel).offset(skip).limit(limit).all()
    
    # Converter com máxima segurança
    result = []
    for imovel in imoveis:
        try:
            # Função auxiliar para conversão segura
            def safe_float(value):
                if value is None:
                    return None
                try:
                    # Verificar se é NaN
                    if str(value).lower() == 'nan':
                        return None
                    return float(value)
                except:
                    return None
            
            def safe_bool(value):
                if value is None:
                    return False
                try:
                    return bool(value)
                except:
                    return False
            
            imovel_dict = {
                'id': imovel.id,
                'nome': imovel.nome or '',
                'endereco': imovel.endereco or '',
                'tipo': imovel.tipo or '',
                'area_total': safe_float(imovel.area_total),
                'area_construida': safe_float(imovel.area_construida),
                'valor_catastral': safe_float(imovel.valor_catastral),
                'valor_mercado': safe_float(imovel.valor_mercado),
                'iptu_anual': safe_float(imovel.iptu_anual),
                'condominio': safe_float(imovel.condominio),
                'alugado': safe_bool(imovel.alugado),
                'ativo': safe_bool(imovel.ativo)
            }
            result.append(imovel_dict)
        except Exception as e:
            # Em caso de erro, pular este imóvel e continuar
            print(f"Aviso: Pulando imóvel ID {imovel.id} devido a erro: {e}")
            continue
    
    return result

@router.post("/", response_model=Imovel)
def create_imovel(
    imovel: ImovelCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    db_imovel = ImovelModel(**imovel.dict())
    db.add(db_imovel)
    db.commit()
    db.refresh(db_imovel)
    return db_imovel

@router.get("/{imovel_id}", response_model=Imovel)
def read_imovel(
    imovel_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    db_imovel = db.query(ImovelModel).filter(ImovelModel.id == imovel_id).first()
    if db_imovel is None:
        raise HTTPException(status_code=404, detail="Imovel not found")
    return db_imovel

@router.put("/{imovel_id}", response_model=Imovel)
def update_imovel(
    imovel_id: int,
    imovel_update: ImovelUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    db_imovel = db.query(ImovelModel).filter(ImovelModel.id == imovel_id).first()
    if db_imovel is None:
        raise HTTPException(status_code=404, detail="Imovel not found")
    
    update_data = imovel_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_imovel, field, value)
    
    db.commit()
    db.refresh(db_imovel)
    return db_imovel

@router.delete("/{imovel_id}")
def delete_imovel(
    imovel_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    db_imovel = db.query(ImovelModel).filter(ImovelModel.id == imovel_id).first()
    if db_imovel is None:
        raise HTTPException(status_code=404, detail="Imovel not found")
    
    db.delete(db_imovel)
    db.commit()
    return {"message": "Imovel deleted successfully"}