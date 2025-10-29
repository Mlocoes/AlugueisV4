"""
Rotas para importação de dados via Excel - Versão Unificada
Sistema inteligente que detecta automaticamente o tipo de dados
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
    - Colunas obrigatórias: Nome (ou variações como "Nome do Imóvel") e Endereço (ou "Endereço do Imóvel")
    - Coluna opcional: Tipo (padrão: Residencial)
    - Outras colunas opcionais: Área Total, Área Construída, Valor Catastral, Valor Mercado, IPTU Anual, Condomínio
    - O sistema tenta identificar automaticamente as colunas por nome
    - Valores monetários em formato brasileiro (vírgula como decimal)
    - Tipo deve ser "Comercial" ou "Residencial" (padrão: Residencial)
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="Arquivo deve ser Excel (.xlsx ou .xls)"
        )
    
    content = await file.read()
    service = ImportacaoAvancadaService()
    result = service.importar_imoveis(content, db)
    
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


def detectar_tipo_arquivo(filename: str, df: pd.DataFrame) -> str:
    """
    Detecta automaticamente o tipo de dados baseado no nome do arquivo e conteúdo
    
    **Critérios de detecção:**
    - Nome do arquivo: proprietarios, imoveis, participacoes, alugueis
    - Colunas específicas para cada tipo
    - Conteúdo dos dados
    """
    filename_lower = filename.lower()
    
    # Detecção por nome do arquivo
    if 'proprietario' in filename_lower or 'owner' in filename_lower:
        return 'proprietarios'
    elif 'imovel' in filename_lower or 'imóvel' in filename_lower or 'property' in filename_lower:
        return 'imoveis'
    elif 'participacao' in filename_lower or 'participação' in filename_lower or 'share' in filename_lower:
        return 'participacoes'
    elif 'aluguel' in filename_lower or 'aluguel' in filename_lower or 'rent' in filename_lower:
        return 'alugueis'
    
    # Detecção por colunas
    columns = [str(col).lower() for col in df.columns]
    
    # Proprietários: tem email, documento, telefone
    if any('email' in col for col in columns) and any('documento' in col or 'cpf' in col for col in columns):
        return 'proprietarios'
    
    # Imóveis: tem endereço, nome/título
    if any('endereço' in col or 'address' in col for col in columns) and any('nome' in col or 'title' in col for col in columns):
        return 'imoveis'
    
    # Participações: tem VALOR próximo de 1.0
    valor_col = None
    for col in df.columns:
        if 'VALOR' in str(col).upper():
            valor_col = col
            break
    
    if valor_col is not None:
        valores = df[valor_col].dropna()
        if len(valores) > 0:
            media_valor = valores.mean()
            if abs(media_valor - 1.0) < 0.1:  # Valores próximos de 1.0
                return 'participacoes'
    
    # Aluguéis: múltiplas planilhas ou formato especial
    try:
        xl = pd.ExcelFile(BytesIO(df.to_excel().encode()))
        if len(xl.sheet_names) > 1:
            return 'alugueis'
    except:
        pass
    
    # Fallback: tentar detectar por conteúdo
    sample_text = ' '.join([str(val) for val in df.iloc[0].values if pd.notna(val)]).lower()
    
    if 'cpf' in sample_text or 'cnpj' in sample_text:
        return 'proprietarios'
    elif 'rua' in sample_text or 'avenida' in sample_text or 'street' in sample_text:
        return 'imoveis'
    
    return 'desconhecido'


@router.post("/upload")
async def upload_arquivo_unificado(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Upload unificado de arquivo Excel - detecta automaticamente o tipo
    
    **Funcionalidades:**
    - Detecção automática do tipo de dados
    - Validação da estrutura do arquivo
    - Preview dos dados antes da importação
    - Importação opcional após análise
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="Arquivo deve ser Excel (.xlsx ou .xls)"
        )
    
    try:
        content = await file.read()
        df = pd.read_excel(BytesIO(content), sheet_name=0)
        
        # Detectar tipo
        tipo_detectado = detectar_tipo_arquivo(file.filename, df)
        
        if tipo_detectado == 'desconhecido':
            return {
                'success': False,
                'tipo_detectado': 'desconhecido',
                'message': 'Não foi possível detectar o tipo de dados automaticamente',
                'sugestoes': [
                    'Verifique se o nome do arquivo contém: proprietarios, imoveis, participacoes, ou alugueis',
                    'Verifique se as colunas estão corretas para o tipo de dados',
                    'Use a análise manual especificando o tipo'
                ],
                'colunas_encontradas': list(df.columns),
                'preview': df.head(3).to_dict('records')
            }
        
        # Análise básica
        analise = {
            'total_linhas': len(df),
            'total_colunas': len(df.columns),
            'colunas_encontradas': list(df.columns),
            'tipo_detectado': tipo_detectado,
            'preview': df.head(5).to_dict('records'),
            'problemas': []
        }
        
        # Validações específicas por tipo detectado
        if tipo_detectado == 'proprietarios':
            required_cols = ['Nome', 'Email']
            missing = [col for col in required_cols if col not in df.columns]
            if missing:
                analise['problemas'].append(f"Colunas obrigatórias faltando: {', '.join(missing)}")
                
        elif tipo_detectado == 'imoveis':
            required_cols = ['Nome', 'Endereço']
            missing = [col for col in required_cols if col not in df.columns]
            if missing:
                analise['problemas'].append(f"Colunas obrigatórias faltando: {', '.join(missing)}")
                
        elif tipo_detectado == 'participacoes':
            valor_col = None
            for col in df.columns:
                if 'VALOR' in str(col).upper():
                    valor_col = col
                    break
            
            if not valor_col:
                analise['problemas'].append("Coluna VALOR não encontrada")
                
        elif tipo_detectado == 'alugueis':
            analise['problemas'].append("Aluguéis requerem formato especial com múltiplas planilhas")
        
        return {
            'success': True,
            'tipo_detectado': tipo_detectado,
            'analise': analise,
            'message': f'Arquivo analisado com sucesso. Tipo detectado: {tipo_detectado}',
            'ready_for_import': len(analise['problemas']) == 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f'Erro ao processar arquivo: {str(e)}'
        )


@router.post("/importar")
async def importar_arquivo_unificado(
    file: UploadFile = File(...),
    confirmar_importacao: bool = False,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Importação unificada de arquivo Excel
    
    **Parâmetros:**
    - file: Arquivo Excel
    - confirmar_importacao: true para executar a importação, false para apenas analisar
    
    **Processo:**
    1. Detecta automaticamente o tipo de dados
    2. Valida a estrutura do arquivo
    3. Se confirmar_importacao=true, executa a importação
    4. Retorna relatório completo
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="Arquivo deve ser Excel (.xlsx ou .xls)"
        )
    
    try:
        content = await file.read()
        df = pd.read_excel(BytesIO(content), sheet_name=0)
        
        # Detectar tipo
        tipo_detectado = detectar_tipo_arquivo(file.filename, df)
        
        if tipo_detectado == 'desconhecido':
            raise HTTPException(
                status_code=400,
                detail="Não foi possível detectar o tipo de dados. Use análise manual ou verifique o arquivo."
            )
        
        service = ImportacaoAvancadaService()
        
        # Executar importação baseada no tipo
        if tipo_detectado == 'proprietarios':
            result = service.importar_proprietarios(content, db)
        elif tipo_detectado == 'imoveis':
            result = service.importar_imoveis(content, db)
        elif tipo_detectado == 'participacoes':
            result = service.importar_participacoes(content, db)
        elif tipo_detectado == 'alugueis':
            result = service.importar_alugueis(content, db)
        else:
            raise HTTPException(status_code=400, detail=f"Tipo não suportado: {tipo_detectado}")
        
        result['tipo_detectado'] = tipo_detectado
        result['arquivo'] = file.filename
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Erro interno durante importação: {str(e)}'
        )
