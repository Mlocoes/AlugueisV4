"""
Rotas para importação de dados via Excel - Versão Avançada
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.core.database import get_db
from app.services.import_service import ImportacaoAvancadaService
from app.core.auth import get_current_active_user
from app.schemas import Usuario
import pandas as pd
from io import BytesIO

router = APIRouter(tags=["import"])


def require_admin(current_user: Usuario = Depends(get_current_active_user)):
    """Verifica se o usuário é administrador"""
    if current_user.tipo != 'administrador':
        raise HTTPException(
            status_code=403,
            detail="Acesso negado. Apenas administradores podem importar dados."
        )
    return current_user


@router.post("/proprietarios")
async def import_proprietarios(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Importa proprietários de um arquivo Excel (.xlsx)
    
    **Estrutura esperada:**
    - Nome, Sobrenome, Documento, Tipo Documento, Endereço, Telefone, Email
    - Documento pode conter formatação (ex: 170.858.698-95)
    - Tipo Documento geralmente é "CPF"
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="Arquivo deve ser Excel (.xlsx ou .xls)"
        )
    
    content = await file.read()
    service = ImportacaoAvancadaService()
    result = service.importar_proprietarios(content, db)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['message'])
    
    return result


@router.post("/imoveis")
async def import_imoveis(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Importa imóveis de um arquivo Excel (.xlsx)
    
    **Estrutura esperada:**
    - Nome, Endereço, Tipo, Área Total, Área Construída, Valor Catastral, Valor Mercado, IPTU Anual, Condomínio
    - Valores monetários em formato brasileiro (vírgula como decimal)
    - Tipo deve ser "Comercial" ou "Residencial"
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="Arquivo deve ser Excel (.xlsx ou .xls)"
        )
    
    content = await file.read()
    service = ImportacaoAvancadaService()
    result = service.importar_imoveis(content, db)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['message'])
    
    return result


@router.post("/participacoes")
async def import_participacoes(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Importa participações de um arquivo Excel (.xlsx)
    
    **Estrutura esperada:**
    - Nome, Endereço, VALOR (sempre próximo de 1.0), [colunas dinâmicas com nomes dos proprietários]
    - Participações como valores decimais entre 0 e 1 (ex: 0.25 para 25%)
    - Soma das participações deve ser 100% (1.0)
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="Arquivo deve ser Excel (.xlsx ou .xls)"
        )
    
    content = await file.read()
    service = ImportacaoAvancadaService()
    result = service.importar_participacoes(content, db)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['message'])
    
    return result


@router.post("/alugueis")
async def import_alugueis(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Importa aluguéis mensais de um arquivo Excel (.xlsx)
    
    **Estrutura especial - MÚLTIPLAS PLANILHAS:**
    - Uma planilha por mês de referência
    - Primeira célula (A1): Data no formato DD/MM/YYYY
    - Colunas: Nome/Endereço imóvel, Valor Total, [valores por proprietário], Taxa Administração
    - Valores podem ser negativos (com hífen)
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="Arquivo deve ser Excel (.xlsx ou .xls)"
        )
    
    content = await file.read()
    service = ImportacaoAvancadaService()
    result = service.importar_alugueis(content, db)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['message'])
    
    return result


@router.post("/analisar/{tipo}")
async def analisar_arquivo_tipo(
    tipo: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Analisa um arquivo Excel específico por tipo e retorna preview dos dados
    
    **Tipos suportados:** proprietarios, imoveis, participacoes, alugueis
    """
    if tipo not in ['proprietarios', 'imoveis', 'participacoes', 'alugueis']:
        raise HTTPException(status_code=400, detail="Tipo inválido")
        
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Arquivo deve ser Excel (.xlsx ou .xls)")
    
    try:
        content = await file.read()
        df = pd.read_excel(BytesIO(content), sheet_name=0)
        
        # Limpar dados para evitar problemas de serialização JSON
        df = df.replace([float('inf'), float('-inf')], None)  # Remover infinitos
        df = df.where(pd.notna(df), None)  # Converter NaN para None
        
        # Converter tipos numpy para tipos Python nativos
        df = df.astype(object).where(pd.notna(df), None)
        
        # Informações básicas
        result = {
            'columns': list(df.columns),
            'total_rows': len(df),
            'data_rows': len(df.dropna(how='all')),
            'preview': df.head(5).to_dict('records'),
            'warnings': []
        }
        
        # Validações específicas por tipo
        if tipo == 'proprietarios':
            required_cols = ['Nome', 'Email', 'Documento']
            missing = [col for col in required_cols if col not in df.columns]
            if missing:
                result['warnings'].append(f"Colunas obrigatórias faltando: {', '.join(missing)}")
                
            # Verificar emails
            if 'Email' in df.columns:
                invalid_emails = 0
                for email in df['Email'].dropna():
                    if '@' not in str(email):
                        invalid_emails += 1
                if invalid_emails > 0:
                    result['warnings'].append(f"{invalid_emails} emails inválidos encontrados")
                    
        elif tipo == 'imoveis':
            required_cols = ['Nome', 'Endereço']
            missing = [col for col in required_cols if col not in df.columns]
            if missing:
                result['warnings'].append(f"Colunas obrigatórias faltando: {', '.join(missing)}")
                
        elif tipo == 'participacoes':
            # Verificar coluna VALOR
            valor_col = None
            for col in df.columns:
                if 'VALOR' in str(col).upper():
                    valor_col = col
                    break
            
            if not valor_col:
                result['warnings'].append("Coluna VALOR não encontrada")
            else:
                # Verificar se VALOR é próximo de 1.0
                invalid_valor = 0
                for valor in df[valor_col].dropna():
                    if abs(float(valor) - 1.0) > 0.01:
                        invalid_valor += 1
                if invalid_valor > 0:
                    result['warnings'].append(f"{invalid_valor} linhas com VALOR diferente de 1.0")
                    
        elif tipo == 'alugueis':
            # Para aluguéis, verificar se tem múltiplas planilhas ou formato especial
            result['warnings'].append("Aluguéis requerem formato especial com múltiplas planilhas (uma por mês)")
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f'Erro ao analisar arquivo: {str(e)}'
        )


@router.post("/analisar")
async def analisar_arquivo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Analisa um arquivo Excel e retorna informações sobre sua estrutura e possíveis problemas
    
    **Retorna:**
    - Informações sobre colunas encontradas
    - Análise de dados vazios ou inválidos
    - Dicas para correção
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="Arquivo deve ser Excel (.xlsx ou .xls)"
        )
    
    try:
        content = await file.read()
        df = pd.read_excel(BytesIO(content), sheet_name=0)
        
        # Limpar dados para evitar problemas de serialização JSON
        df = df.replace([float('inf'), float('-inf')], None)  # Remover infinitos
        df = df.where(pd.notna(df), None)  # Converter NaN para None
        
        # Converter tipos numpy para tipos Python nativos
        df = df.astype(object).where(pd.notna(df), None)
        
        analise = {
            'total_linhas': len(df),
            'total_colunas': len(df.columns),
            'colunas_encontradas': list(df.columns),
            'colunas_obrigatorias': ['Nome', 'Sobrenome', 'Documento', 'Tipo Documento', 'Endereço', 'Telefone', 'Email'],
            'problemas': [],
            'estatisticas': {}
        }
        
        # Verificar colunas obrigatórias
        colunas_faltando = [col for col in analise['colunas_obrigatorias'] if col not in df.columns]
        if colunas_faltando:
            analise['problemas'].append({
                'tipo': 'colunas_faltando',
                'mensagem': f'Colunas obrigatórias faltando: {", ".join(colunas_faltando)}'
            })
        
        # Analisar dados
        estatisticas = {}
        for col in analise['colunas_obrigatorias']:
            if col in df.columns:
                vazios = df[col].isnull().sum() + (df[col].astype(str).str.strip() == '').sum()
                estatisticas[col] = {
                    'vazios': int(vazios),
                    'preenchidos': len(df) - int(vazios)
                }
        
        # Verificações específicas
        if 'Email' in df.columns:
            emails_invalidos = 0
            for email in df['Email']:
                if pd.notna(email) and '@' not in str(email):
                    emails_invalidos += 1
            if emails_invalidos > 0:
                analise['problemas'].append({
                    'tipo': 'emails_invalidos',
                    'mensagem': f'{emails_invalidos} emails inválidos (sem @)'
                })
        
        if 'Documento' in df.columns:
            docs_invalidos = 0
            for doc in df['Documento']:
                if pd.notna(doc):
                    doc_limpo = ''.join(filter(str.isdigit, str(doc)))
                    if len(doc_limpo) < 11:
                        docs_invalidos += 1
            if docs_invalidos > 0:
                analise['problemas'].append({
                    'tipo': 'documentos_invalidos',
                    'mensagem': f'{docs_invalidos} documentos com menos de 11 dígitos'
                })
        
        analise['estatisticas'] = estatisticas
        
        # Amostra dos dados
        analise['amostra'] = df.head(3).to_dict('records')
        
        return {
            'success': True,
            'analise': analise,
            'message': 'Análise concluída'
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f'Erro ao analisar arquivo: {str(e)}'
        )
