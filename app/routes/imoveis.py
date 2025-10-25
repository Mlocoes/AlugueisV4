from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_active_user, get_current_admin_user
from app.core.permissions import filter_inactive_records
from app.schemas import Imovel, ImovelCreate, ImovelUpdate
from app.models.imovel import Imovel as ImovelModel
from app.models.usuario import Usuario
from decimal import Decimal

router = APIRouter()

@router.get("/")
def read_imoveis(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    # Aplicar filtros de permissão
    query = db.query(ImovelModel)
    query = filter_inactive_records(query, current_user)
    
    imoveis = query.offset(skip).limit(limit).all()
    
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
    current_user: Usuario = Depends(get_current_admin_user)
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
    current_user: Usuario = Depends(get_current_admin_user)
):
    db_imovel = db.query(ImovelModel).filter(ImovelModel.id == imovel_id).first()
    if db_imovel is None:
        raise HTTPException(status_code=404, detail="Imovel not found")
    
    update_data = imovel_update.dict(exclude_unset=True)
    # Converter valores numéricos para Decimal quando necessário (evitar problemas de tipo)
    decimal_fields = {
        'area_total', 'area_construida', 'valor_catastral', 'valor_mercado', 'iptu_anual', 'condominio'
    }
    for k, v in list(update_data.items()):
        if k in decimal_fields and v is not None:
            try:
                # Aceitar floats, ints ou strings; converter com Decimal(str(...)) para precisão
                if isinstance(v, Decimal):
                    update_data[k] = v
                else:
                    update_data[k] = Decimal(str(v))
            except Exception:
                # Se conversão falhar, remover o campo para evitar erro de banco
                update_data.pop(k, None)
    for field, value in update_data.items():
        setattr(db_imovel, field, value)

    # Commit com tratamento para capturar erros e retornar detalhes úteis
    try:
        db.commit()
        db.refresh(db_imovel)
    except Exception as e:
        db.rollback()
        # Log curto no stdout para debugging (uvicorn/console deve mostrar)
        print(f"Erro ao atualizar imóvel ID {imovel_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar imóvel: {str(e)}")
    
    # Aplicar conversão segura como no GET para evitar erro de serialização
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
    
    # Retornar dicionário convertido em vez do objeto direto
    return {
        'id': db_imovel.id,
        'nome': db_imovel.nome or '',
        'endereco': db_imovel.endereco or '',
        'tipo': db_imovel.tipo or '',
        'area_total': safe_float(db_imovel.area_total),
        'area_construida': safe_float(db_imovel.area_construida),
        'valor_catastral': safe_float(db_imovel.valor_catastral),
        'valor_mercado': safe_float(db_imovel.valor_mercado),
        'iptu_anual': safe_float(db_imovel.iptu_anual),
        'condominio': safe_float(db_imovel.condominio),
        'alugado': safe_bool(db_imovel.alugado),
        'ativo': safe_bool(db_imovel.ativo)
    }

@router.delete("/{imovel_id}")
def delete_imovel(
    imovel_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)
):
    db_imovel = db.query(ImovelModel).filter(ImovelModel.id == imovel_id).first()
    if db_imovel is None:
        raise HTTPException(status_code=404, detail="Imovel not found")
    
    db.delete(db_imovel)
    db.commit()
    return {"message": "Imovel deleted successfully"}