"""
Serviço de importação de dados a partir de arquivos Excel - Versão Avançada
Suporte para múltiplas planilhas, validações específicas e formatos brasileiros
"""
from typing import List, Dict, Any, Tuple, Optional
import re
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
try:
    import pandas as pd
    import openpyxl
except Exception:
    pd = None
    openpyxl = None

from io import BytesIO
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.usuario import Usuario
from app.models.imovel import Imovel
from app.models.aluguel import AluguelMensal
from app.models.participacao import Participacao


class ImportacaoAvancadaService:
    """Serviço avançado para importação de dados via Excel"""

    def __init__(self):
        self._ensure_dependencies()

    def _ensure_dependencies(self):
        """Garante que as dependências necessárias estão instaladas"""
        if pd is None or openpyxl is None:
            raise RuntimeError(
                "Dependências necessárias não encontradas. Instale: pip install pandas openpyxl"
            )

    @staticmethod
    def limpar_cpf(cpf_str: str) -> str:
        """Remove formatação do CPF/CNPJ deixando apenas números"""
        if not cpf_str:
            return ""
        return re.sub(r'[^\d]', '', str(cpf_str))

    @staticmethod
    def validar_cpf(cpf: str) -> bool:
        """Valida formato básico do CPF"""
        cpf = ImportacaoAvancadaService.limpar_cpf(cpf)
        return len(cpf) >= 11  # CPF tem 11 dígitos, CNPJ tem 14

    @staticmethod
    def parse_valor_monetario(valor_str) -> Optional[Decimal]:
        """Converte string monetária brasileira ou americana para Decimal"""
        # Tratamento para None
        if valor_str is None:
            return None

        # Se já for numérico (int/float/Decimal), converter diretamente preservando valor
        if isinstance(valor_str, (int, float, Decimal)):
            try:
                return Decimal(str(valor_str))
            except Exception:
                return None

        # A partir daqui, tratar como string
        s = str(valor_str).strip()
        if s in ['', '-']:
            return None

        negativo = False
        if s.startswith('-'):
            negativo = True
            s = s[1:].strip()

        # Remove "R$", espaços e outros caracteres não numéricos exceto vírgula e ponto
        s = re.sub(r'[R$\s]', '', s)

        # Detectar formato: se tem vírgula E ponto, tentar identificar qual é o separador decimal
        # Ex.:
        #  - Brasileiro: 1.234,56 -> '.' milhares, ',' decimal
        #  - Americano: 2,500.00 -> ',' milhares, '.' decimal
        if ',' in s and '.' in s:
            # Determinar qual separador aparece por último; o separador decimal normalmente
            # aparece mais à direita e costuma ter 2 casas decimais.
            last_dot = s.rfind('.')
            last_comma = s.rfind(',')
            # Se o ponto vem depois da vírgula e tem até 2 dígitos após ele, é provavelmente o separador decimal (US)
            if last_dot > last_comma and (len(s) - last_dot - 1) <= 2:
                # Formato americano: remover vírgulas (milhares)
                s = s.replace(',', '')
            # Se a vírgula vem depois do ponto e tem até 2 dígitos após ela, é formato brasileiro
            elif last_comma > last_dot and (len(s) - last_comma - 1) <= 2:
                s = s.replace('.', '').replace(',', '.')
            else:
                # Fallback conservador: remover separadores de milhares (vírgulas)
                s = s.replace(',', '')
        elif ',' in s and '.' not in s:
            # Apenas vírgula: 1234,56 -> 1234.56
            s = s.replace(',', '.')
        # else: apenas ponto ou nenhum separador -> manter

        try:
            valor = Decimal(s)
            return -valor if negativo else valor
        except (InvalidOperation, ValueError):
            return None

    @staticmethod
    def parse_data(data_str: str) -> Optional[date]:
        """Converte string de data para date object"""
        if not data_str or str(data_str).strip() in ['', '-']:
            return None

        formatos = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y']
        for fmt in formatos:
            try:
                return datetime.strptime(str(data_str).strip(), fmt).date()
            except ValueError:
                continue
        return None

    def importar_proprietarios(self, file_content: bytes, db: Session) -> Dict[str, Any]:
        """Importa proprietários do Excel"""
        try:
            df = pd.read_excel(BytesIO(file_content), sheet_name=0)

            # Validar colunas obrigatórias
            colunas_esperadas = ['Nome', 'Sobrenome', 'Documento', 'Tipo Documento', 'Endereço', 'Telefone', 'Email']
            colunas_faltando = [col for col in colunas_esperadas if col not in df.columns]
            if colunas_faltando:
                return {
                    'success': False,
                    'message': f'Colunas obrigatórias faltando: {", ".join(colunas_faltando)}. Colunas encontradas: {", ".join(df.columns)}'
                }

            registros_importados = 0
            erros = []
            linhas_processadas = 0

            for idx, row in df.iterrows():
                linhas_processadas += 1
                
                try:
                    # Limpar e validar dados
                    nome = str(row['Nome']).strip()
                    sobrenome = str(row.get('Sobrenome', '')).strip()
                    documento = self.limpar_cpf(str(row['Documento']))
                    tipo_documento = str(row.get('Tipo Documento', 'CPF')).strip().upper()
                    endereco = str(row.get('Endereço', '')).strip()
                    telefone = str(row.get('Telefone', '')).strip()
                    email = str(row['Email']).strip().lower()

                    # Validações
                    if not nome:
                        erros.append(f"Linha {idx+2}: Nome é obrigatório (encontrado: '{row.get('Nome', '')}')")
                        continue

                    if not email or '@' not in email:
                        erros.append(f"Linha {idx+2}: Email inválido (encontrado: '{row.get('Email', '')}')")
                        continue

                    if not self.validar_cpf(documento):
                        erros.append(f"Linha {idx+2}: Documento inválido (encontrado: '{row.get('Documento', '')}' -> '{documento}')")
                        continue

                    # Verificar duplicata
                    existente = db.query(Usuario).filter(Usuario.documento == documento).first()
                    if existente:
                        erros.append(f"Linha {idx+2}: Proprietário com documento {documento} já existe (nome: {existente.nome})")
                        continue

                    # Criar proprietário
                    proprietario = Usuario(
                        nome=nome,
                        sobrenome=sobrenome,
                        documento=documento,
                        tipo_documento=tipo_documento,
                        endereco=endereco,
                        telefone=telefone,
                        email=email,
                        tipo='usuario',  # proprietário
                        username=email,  # usar email como username
                        hashed_password='senha123',  # senha padrão
                        ativo=True
                    )

                    db.add(proprietario)
                    registros_importados += 1

                except Exception as e:
                    erros.append(f"Linha {idx+2}: Erro ao processar - {str(e)} (dados: {dict(row)})")

            db.commit()

            return {
                'success': True,
                'message': f'Importação concluída. {registros_importados} proprietários importados de {linhas_processadas} linhas processadas.',
                'registros_importados': registros_importados,
                'linhas_processadas': linhas_processadas,
                'erros': erros
            }

        except Exception as e:
            db.rollback()
            return {
                'success': False,
                'message': f'Erro na importação: {str(e)}'
            }

    def importar_imoveis(self, file_content: bytes, db: Session) -> Dict[str, Any]:
        """Importa imóveis do Excel"""
        try:
            # Primeiro ler para identificar as colunas
            df_preview = pd.read_excel(BytesIO(file_content), sheet_name=0, nrows=1)
            colunas = df_preview.columns.tolist()
            
            # Criar converters para colunas monetárias - forçar leitura como string
            converters = {}
            colunas_monetarias = [
                'área total', 'area total', 'total area',
                'área construída', 'area construida', 'constructed area', 
                'valor catastral', 'cadastral value',
                'valor de mercado', 'valor mercado', 'market value',
                'iptu', 'iptu anual', 'annual iptu',
                'condomínio', 'condominio', 'hoa fee'
            ]
            
            for i, col in enumerate(colunas):
                col_padronizada = col.lower().strip()
                if any(monetaria in col_padronizada for monetaria in colunas_monetarias):
                    converters[col] = str  # Forçar leitura como string para preservar formato
            
            df = pd.read_excel(BytesIO(file_content), sheet_name=0, converters=converters)

            # Mapeamento flexível de colunas
            mapeamento = self.mapear_colunas_imoveis(df.columns.tolist())
            
            if not mapeamento['nome'] or not mapeamento['endereco']:
                return {
                    'success': False,
                    'message': 'Não foi possível identificar as colunas obrigatórias (Nome/Endereço do imóvel)'
                }

            registros_importados = 0
            erros = []

            for idx, row in df.iterrows():
                try:
                    # Limpar e validar dados usando mapeamento
                    nome = str(row[mapeamento['nome']]).strip()
                    endereco = str(row[mapeamento['endereco']]).strip()
                    tipo = str(row.get(mapeamento['tipo'], 'Residencial')).strip() if mapeamento['tipo'] else 'Residencial'

                    # Validar tipo
                    tipos_validos = ['Comercial', 'Residencial']
                    if tipo not in tipos_validos:
                        erros.append(f"Linha {idx+2}: Tipo deve ser 'Comercial' ou 'Residencial'")
                        continue

                    # Verificar duplicata por nome + endereço
                    existente = db.query(Imovel).filter(
                        Imovel.nome == nome,
                        Imovel.endereco == endereco
                    ).first()
                    if existente:
                        erros.append(f"Linha {idx+2}: Imóvel '{nome}' já existe neste endereço")
                        continue

                    # Parsear valores numéricos usando mapeamento
                    area_total = self.parse_valor_monetario(str(row.get(mapeamento['area_total'], ''))) if mapeamento['area_total'] else None
                    area_construida = self.parse_valor_monetario(str(row.get(mapeamento['area_construida'], ''))) if mapeamento['area_construida'] else None
                    valor_catastral = self.parse_valor_monetario(str(row.get(mapeamento['valor_catastral'], ''))) if mapeamento['valor_catastral'] else None
                    valor_mercado = self.parse_valor_monetario(str(row.get(mapeamento['valor_mercado'], ''))) if mapeamento['valor_mercado'] else None
                    iptu_anual = self.parse_valor_monetario(str(row.get(mapeamento['iptu_anual'], ''))) if mapeamento['iptu_anual'] else None
                    condominio = self.parse_valor_monetario(str(row.get(mapeamento['condominio'], ''))) if mapeamento['condominio'] else None

                    # Criar imóvel
                    imovel = Imovel(
                        nome=nome,
                        endereco=endereco,
                        tipo=tipo,
                        area_total=area_total,
                        area_construida=area_construida,
                        valor_catastral=valor_catastral,
                        valor_mercado=valor_mercado,
                        iptu_anual=iptu_anual,
                        condominio=condominio,
                        alugado=False,
                        ativo=True
                    )

                    db.add(imovel)
                    registros_importados += 1

                except Exception as e:
                    erros.append(f"Linha {idx+2}: Erro ao processar - {str(e)}")

            db.commit()

            return {
                'success': True,
                'message': f'Importação concluída. {registros_importados} imóveis importados.',
                'registros_importados': registros_importados,
                'erros': erros
            }

        except Exception as e:
            db.rollback()
            return {
                'success': False,
                'message': f'Erro na importação: {str(e)}'
            }

    def importar_participacoes(self, file_content: bytes, db: Session) -> Dict[str, Any]:
        """Importa participações do Excel (formato com valores decimais 0-1)"""
        try:
            df = pd.read_excel(BytesIO(file_content), sheet_name=0)

            # Validar colunas mínimas
            if len(df.columns) < 3:
                return {
                    'success': False,
                    'message': 'Arquivo deve ter pelo menos 3 colunas: Nome, Endereço, VALOR'
                }

            # Mapeamento flexível de colunas
            mapeamento = self.mapear_colunas_participacoes(df.columns.tolist())
            
            if not mapeamento['nome_imovel']:
                return {
                    'success': False,
                    'message': 'Não foi possível identificar a coluna do nome do imóvel'
                }
            
            if not mapeamento['valor_total']:
                return {
                    'success': False,
                    'message': 'Coluna VALOR é obrigatória'
                }

            registros_importados = 0
            erros = []

            for idx, row in df.iterrows():
                try:
                    nome_imovel = str(row[mapeamento['nome_imovel']]).strip()
                    valor_total = row[mapeamento['valor_total']]

                    # Validar VALOR (deve ser próximo de 1.0 com tolerância)
                    if pd.isna(valor_total) or abs(float(valor_total) - 1.0) > 0.01:
                        erros.append(f"Linha {idx+2}: VALOR deve ser próximo de 1.0 (100%) - encontrado: {valor_total}")
                        continue

                    # Buscar imóvel por nome
                    imovel = db.query(Imovel).filter(
                        Imovel.nome.ilike(f"%{nome_imovel}%")
                    ).first()

                    if not imovel:
                        # Tentar buscar por endereço também
                        imovel = db.query(Imovel).filter(Imovel.endereco.ilike(f'%{nome_imovel}%')).first()
                    if not imovel:
                        # Listar imóveis similares para debug
                        imoveis_similares = db.query(Imovel).filter(
                            Imovel.nome.ilike(f"%{nome_imovel.split()[0]}%")
                        ).limit(3).all()
                        similares = [i.nome for i in imoveis_similares]
                        erros.append(f"Linha {idx+2}: Imóvel '{nome_imovel}' não encontrado. Imóveis similares: {similares}")
                        continue

                    # Processar participações dos proprietários (colunas dinâmicas)
                    participacoes_imovel = []
                    soma_participacoes = Decimal('0')

                    for col_name in df.columns:
                        # Pular colunas do imóvel
                        if col_name == mapeamento['nome_imovel'] or col_name == mapeamento.get('endereco_imovel', '') or col_name == mapeamento['valor_total']:
                            continue
                            
                        proprietario_nome = str(col_name).strip()
                        participacao_valor = row[col_name]

                        if pd.isna(participacao_valor) or participacao_valor == 0:
                            continue  # Pular valores vazios ou zero

                        # Validar que seja um número decimal entre 0 e 1
                        try:
                            participacao_decimal = Decimal(str(participacao_valor))
                            if participacao_decimal <= 0 or participacao_decimal > 1:
                                erros.append(f"Linha {idx+2}: Participação de '{proprietario_nome}' deve ser entre 0 e 1 (encontrado: {participacao_valor})")
                                continue
                        except (ValueError, TypeError):
                            erros.append(f"Linha {idx+2}: Participação de '{proprietario_nome}' deve ser um número (encontrado: {participacao_valor})")
                            continue

                        # Buscar proprietário por nome
                        proprietario = db.query(Usuario).filter(
                            Usuario.nome.ilike(f"%{proprietario_nome}%")
                        ).first()

                        if not proprietario:
                            # Listar proprietários similares para debug
                            proprietarios_similares = db.query(Usuario).filter(
                                Usuario.nome.ilike(f"%{proprietario_nome.split()[0]}%")
                            ).limit(3).all()
                            similares = [p.nome for p in proprietarios_similares]
                            erros.append(f"Linha {idx+2}: Proprietário '{proprietario_nome}' não encontrado. Proprietários similares: {similares}")
                            continue

                        participacoes_imovel.append({
                            'proprietario': proprietario,
                            'participacao': participacao_decimal
                        })
                        soma_participacoes += participacao_decimal

                    # Validar soma das participações (com tolerância)
                    if abs(soma_participacoes - Decimal('1')) > Decimal('0.01'):  # 1% de tolerância
                        erros.append(f"Linha {idx+2}: Soma das participações deve ser 100% (atual: {soma_participacoes * 100:.2f}%)")
                        continue

                    # Salvar participações no banco
                    for part in participacoes_imovel:
                        # Verificar se já existe
                        existente = db.query(Participacao).filter(
                            Participacao.id_imovel == imovel.id,
                            Participacao.id_proprietario == part['proprietario'].id
                        ).first()
                        
                        if existente:
                            # Atualizar
                            existente.participacao = part['participacao']
                            db.add(existente)
                        else:
                            # Criar nova
                            nova_participacao = Participacao(
                                id_imovel=imovel.id,
                                id_proprietario=part['proprietario'].id,
                                participacao=part['participacao'],
                                data_cadastro=date.today()
                            )
                            db.add(nova_participacao)
                        
                        registros_importados += 1

                except Exception as e:
                    erros.append(f"Linha {idx+2}: Erro ao processar - {str(e)}")

            db.commit()

            return {
                'success': True,
                'message': f'Importação concluída. {registros_importados} participações importadas.',
                'registros_importados': registros_importados,
                'erros': erros
            }

        except Exception as e:
            db.rollback()
            return {
                'success': False,
                'message': f'Erro na importação: {str(e)}'
            }


    @staticmethod
    def mapear_colunas_imoveis(colunas: List[str]) -> Dict[str, str]:
        """Mapeia colunas do Excel para campos de imóveis de forma flexível"""
        mapeamento = {
            'nome': None,
            'endereco': None,
            'tipo': None,
            'area_total': None,
            'area_construida': None,
            'valor_catastral': None,
            'valor_mercado': None,
            'iptu_anual': None,
            'condominio': None
        }
        
        # Padronizar nomes das colunas para comparação
        colunas_padronizadas = [col.lower().strip() for col in colunas]
        
        # Mapeamentos possíveis para cada campo
        mapeamentos_possiveis = {
            'nome': ['nome', 'imóvel', 'imovel', 'propriedade'],
            'endereco': ['endereço', 'endereco', 'localização', 'local', 'rua', 'avenida'],
            'tipo': ['tipo', 'categoria'],
            'area_total': ['área total', 'area total', 'total area'],
            'area_construida': ['área construída', 'area construida', 'constructed area'],
            'valor_catastral': ['valor catastral', 'cadastral value'],
            'valor_mercado': ['valor de mercado', 'valor mercado', 'market value'],
            'iptu_anual': ['iptu', 'iptu anual', 'annual iptu'],
            'condominio': ['condomínio', 'condominio', 'hoa fee']
        }
        
        # Tentar encontrar correspondências
        for campo, possibilidades in mapeamentos_possiveis.items():
            for possibilidade in possibilidades:
                if possibilidade in colunas_padronizadas:
                    idx = colunas_padronizadas.index(possibilidade)
                    mapeamento[campo] = colunas[idx]
                    break
        
        return mapeamento

    @staticmethod
    def mapear_colunas_participacoes(colunas: List[str]) -> Dict[str, str]:
        """Mapeia colunas do Excel para campos de participações de forma flexível"""
        mapeamento = {
            'nome_imovel': None,
            'endereco_imovel': None,
            'valor_total': None
        }
        
        # Padronizar nomes das colunas para comparação
        colunas_padronizadas = [col.lower().strip() for col in colunas]
        
        # Mapeamentos possíveis para cada campo
        mapeamentos_possiveis = {
            'nome_imovel': ['nome', 'nome do imóvel', 'imóvel', 'imovel', 'propriedade'],
            'endereco_imovel': ['endereço', 'endereco', 'localização', 'local', 'rua', 'avenida'],
            'valor_total': ['valor', 'valor total', 'total']
        }
        
        # Tentar encontrar correspondências
        for campo, possibilidades in mapeamentos_possiveis.items():
            for possibilidade in possibilidades:
                if possibilidade in colunas_padronizadas:
                    idx = colunas_padronizadas.index(possibilidade)
                    mapeamento[campo] = colunas[idx]
                    break
        
        return mapeamento

    def importar_alugueis(self, file_content: bytes, db: Session) -> Dict[str, Any]:
        """Importa aluguéis mensais de múltiplas planilhas Excel"""
        try:
            xl = pd.ExcelFile(BytesIO(file_content))
            registros_importados = 0
            erros = []

            for sheet_name in xl.sheet_names:
                try:
                    # Primeiro, ler apenas para determinar o número de colunas
                    df_preview = pd.read_excel(xl, sheet_name=sheet_name, header=None, nrows=5)
                    num_cols = len(df_preview.columns)

                    # Usar converters para forçar leitura como string das colunas monetárias
                    # Isso previne que pandas converta automaticamente valores como "49.891,92" para float
                    converters = {}
                    for i in range(num_cols):
                        if i == 0:
                            converters[i] = str  # Nome do imóvel
                        else:
                            converters[i] = str  # Valores monetários - preservar formato original

                    df = pd.read_excel(xl, sheet_name=sheet_name, header=None, converters=converters)
                    
                    # Verificar se há dados suficientes
                    if df.empty or len(df) < 2:
                        erros.append(f"Planilha '{sheet_name}': Dados insuficientes")
                        continue
                    
                    # Extrair data de referência da célula A1
                    data_ref_str = str(df.iloc[0, 0]).strip()
                    try:
                        # Tentar diferentes formatos de data
                        if 'T' in data_ref_str:
                            # Formato ISO com timezone
                            data_referencia = datetime.fromisoformat(data_ref_str.replace('Z', '+00:00')).date()
                        elif len(data_ref_str.split('-')[0]) == 4:
                            # Formato YYYY-MM-DD
                            if ' ' in data_ref_str:
                                # Com hora: YYYY-MM-DD HH:MM:SS
                                data_referencia = datetime.strptime(data_ref_str.split(' ')[0], '%Y-%m-%d').date()
                            else:
                                # Apenas data: YYYY-MM-DD
                                data_referencia = datetime.strptime(data_ref_str, '%Y-%m-%d').date()
                        else:
                            # Formato brasileiro DD/MM/YYYY
                            data_referencia = datetime.strptime(data_ref_str, '%d/%m/%Y').date()
                    except ValueError as e:
                        erros.append(f"Planilha '{sheet_name}': Data inválida '{data_ref_str}' - {str(e)}")
                        continue

                    # Os cabeçalhos estão na linha 0, colunas 1 em diante
                    headers = df.iloc[0, 1:]  # Pular a coluna da data
                    
                    # Pular a linha dos cabeçalhos para os dados
                    df_data = df[1:]
                    
                    # Remover linhas vazias
                    df_data = df_data.dropna(how='all')
                    
                    if df_data.empty:
                        erros.append(f"Planilha '{sheet_name}': Dados insuficientes")
                        continue
                    
                    # Verificar se a primeira linha de dados tem a estrutura esperada
                    first_data_row = df_data.iloc[0] if len(df_data) > 0 else None
                    if first_data_row is None:
                        erros.append(f"Planilha '{sheet_name}': Dados insuficientes")
                        continue
                    
                    # A estrutura esperada é:
                    # Coluna 0: Nome do imóvel
                    # Coluna 1: Valor Total
                    # Colunas 2 até penúltima: Valores por proprietário (com nomes específicos)
                    # Última coluna: Taxa de Administração
                    
                    # Definir índices das colunas (ajustados pois headers começa da coluna 1)
                    imovel_col = 0  # Sempre a primeira coluna dos dados
                    valor_total_col = 1  # Sempre a segunda coluna dos dados
                    taxa_admin_col = len(df_data.columns) - 1  # Última coluna dos dados
                    
                    # Colunas dos proprietários são da 3ª até a penúltima dos dados
                    # Mas mapeiam para os cabeçalhos (que começam do índice 0 dos headers)
                    proprietario_cols = []
                    for i in range(2, len(df_data.columns) - 1):
                        header_idx = i - 1  # Headers começa do índice 0
                        if header_idx < len(headers):
                            nome_proprietario = str(headers.iloc[header_idx]).strip()
                            if nome_proprietario and nome_proprietario.lower() not in ['nan', 'none', '']:
                                proprietario_cols.append((i, nome_proprietario))
                    
                    # Mapear proprietários pelos nomes das colunas do Excel
                    proprietarios_mapeados = []
                    for col_idx, nome_excel in proprietario_cols:
                        # Buscar proprietário por nome (case insensitive, partial match)
                        proprietario = None
                        for tipo in ['usuario', 'proprietario']:
                            proprietario = db.query(Usuario).filter(
                                Usuario.tipo == tipo,
                                Usuario.nome.ilike(f'%{nome_excel}%')
                            ).first()
                            if proprietario:
                                break
                        
                        if not proprietario:
                            # Tentar buscar por nome completo (nome + sobrenome)
                            partes_nome = nome_excel.split()
                            if len(partes_nome) >= 2:
                                proprietario = db.query(Usuario).filter(
                                    Usuario.tipo.in_(['usuario', 'proprietario']),
                                    Usuario.nome.ilike(f'%{partes_nome[0]}%'),
                                    Usuario.sobrenome.ilike(f'%{partes_nome[1]}%')
                                ).first()
                        
                        if proprietario:
                            proprietarios_mapeados.append((col_idx, proprietario))
                        else:
                            erros.append(f"Planilha '{sheet_name}': Proprietário '{nome_excel}' não encontrado")
                    
                    if not proprietarios_mapeados:
                        erros.append(f"Planilha '{sheet_name}': Nenhum proprietário mapeado")
                        continue

                    # Processar cada linha (imóvel)
                    for idx, row in df_data.iterrows():
                        try:
                            imovel_nome = str(row.iloc[imovel_col]).strip()
                            if not imovel_nome or imovel_nome.lower() in ['nan', 'none', '']:
                                continue
                            
                            # Buscar imóvel por nome
                            imovel = db.query(Imovel).filter(Imovel.nome.ilike(f'%{imovel_nome}%')).first()
                            if not imovel:
                                # Tentar buscar por endereço também
                                imovel = db.query(Imovel).filter(Imovel.endereco.ilike(f'%{imovel_nome}%')).first()
                            if not imovel:
                                erros.append(f"Linha {idx+3} planilha '{sheet_name}': Imóvel '{imovel_nome}' não encontrado")
                                continue
                            
                            # Valor total do aluguel
                            valor_total_str = str(row.iloc[valor_total_col]).strip()
                            valor_total = self.parse_valor_monetario(valor_total_str)
                            if valor_total is None:
                                erros.append(f"Linha {idx+3} planilha '{sheet_name}': Valor total inválido '{valor_total_str}'")
                                continue
                            
                            # Taxa de administração (opcional)
                            taxa_admin_str = str(row.iloc[taxa_admin_col]).strip()
                            taxa_admin = self.parse_valor_monetario(taxa_admin_str) or Decimal('0')
                            
                            # Processar valores por proprietário mapeado
                            for col_idx, proprietario in proprietarios_mapeados:
                                valor_prop_str = str(row.iloc[col_idx]).strip()
                                if valor_prop_str.lower() in ['nan', 'none', '']:
                                    continue
                                
                                # Limpar valor
                                valor_proprietario = self.parse_valor_monetario(valor_prop_str)
                                if valor_proprietario is None:
                                    continue
                                
                                # Verificar se já existe registro para este mês/proprietário/imóvel
                                existing = db.query(AluguelMensal).filter(
                                    AluguelMensal.id_imovel == imovel.id,
                                    AluguelMensal.id_proprietario == proprietario.id,
                                    AluguelMensal.data_referencia == data_referencia
                                ).first()
                                
                                if existing:
                                    # Atualizar
                                    existing.valor_total = valor_total
                                    existing.valor_proprietario = valor_proprietario
                                    existing.taxa_administracao = taxa_admin
                                    existing.atualizado_em = func.now()
                                else:
                                    # Criar novo
                                    novo_aluguel = AluguelMensal(
                                        id_imovel=imovel.id,
                                        id_proprietario=proprietario.id,
                                        data_referencia=data_referencia,
                                        valor_total=valor_total,
                                        valor_proprietario=valor_proprietario,
                                        taxa_administracao=taxa_admin
                                    )
                                    db.add(novo_aluguel)
                                
                                registros_importados += 1
                        
                        except Exception as e:
                            erros.append(f"Linha {idx+3} planilha '{sheet_name}': Erro ao processar - {str(e)}")
                
                except Exception as e:
                    erros.append(f"Planilha '{sheet_name}': Erro geral - {str(e)}")
            
            db.commit()
            
            return {
                'success': True,
                'message': f'Importação concluída. {registros_importados} registros de aluguel importados.',
                'registros_importados': registros_importados,
                'erros': erros
            }
        
        except Exception as e:
            db.rollback()
            return {
                'success': False,
                'message': f'Erro na importação: {str(e)}'
            }

