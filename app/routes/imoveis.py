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
    q: str = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    # Aplicar filtros de permissão
    query = db.query(ImovelModel)
    query = filter_inactive_records(query, current_user)
    
    # Filtro por busca
    if q:
        search_term = f"%{q}%"
        query = query.filter(
            (ImovelModel.endereco.ilike(search_term)) |
            (ImovelModel.nome.ilike(search_term)) |
            (ImovelModel.tipo.ilike(search_term))
        )
    
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

@router.get("/export")
def export_imoveis(
    endereco: str = None,
    tipo: str = None,
    status: str = None,
    valor_min: float = None,
    valor_max: float = None,
    format: str = "excel",
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Exportar imóveis filtrados para Excel ou CSV
    """
    from fastapi.responses import StreamingResponse
    import io
    import pandas as pd
    from datetime import datetime
    
    # Aplicar filtros de permissão
    query = db.query(ImovelModel)
    query = filter_inactive_records(query, current_user)
    
    # Aplicar filtros de busca
    if endereco:
        search_term = f"%{endereco}%"
        query = query.filter(
            (ImovelModel.endereco.ilike(search_term)) |
            (ImovelModel.nome.ilike(search_term))
        )
    
    if tipo and tipo != "Todos":
        query = query.filter(ImovelModel.tipo == tipo)
    
    if status and status != "Todos":
        if status == "alugado":
            query = query.filter(ImovelModel.alugado == True)
        elif status == "disponivel":
            query = query.filter(ImovelModel.alugado == False)
    
    if valor_min is not None or valor_max is not None:
        if valor_min is not None:
            query = query.filter(ImovelModel.valor_mercado >= valor_min)
        if valor_max is not None:
            query = query.filter(ImovelModel.valor_mercado <= valor_max)
    
    imoveis = query.all()
    
    # Preparar dados para exportação
    data = []
    for imovel in imoveis:
        data.append({
            'ID': imovel.id,
            'Nome': imovel.nome or '',
            'Endereço': imovel.endereco or '',
            'Tipo': imovel.tipo or '',
            'Cidade': imovel.cidade or '',
            'Estado': imovel.estado or '',
            'Área Total (m²)': float(imovel.area_total) if imovel.area_total else '',
            'Área Construída (m²)': float(imovel.area_construida) if imovel.area_construida else '',
            'Valor Catastral': float(imovel.valor_catastral) if imovel.valor_catastral else '',
            'Valor Mercado': float(imovel.valor_mercado) if imovel.valor_mercado else '',
            'IPTU Anual': float(imovel.iptu_anual) if imovel.iptu_anual else '',
            'Condomínio': float(imovel.condominio) if imovel.condominio else '',
            'Status': 'Alugado' if imovel.alugado else 'Disponível',
            'Ativo': 'Sim' if imovel.ativo else 'Não'
        })
    
    df = pd.DataFrame(data)
    
    # Criar buffer para o arquivo
    buffer = io.BytesIO()
    
    if format.lower() == "csv":
        # Exportar como CSV
        df.to_csv(buffer, index=False, encoding='utf-8-sig')
        buffer.seek(0)
        
        filename = f"imoveis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return StreamingResponse(
            io.BytesIO(buffer.getvalue()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    else:
        # Exportar como Excel
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Imóveis', index=False)
            
            # Ajustar largura das colunas
            worksheet = writer.sheets['Imóveis']
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
        
        filename = f"imoveis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return StreamingResponse(
            io.BytesIO(buffer.getvalue()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )