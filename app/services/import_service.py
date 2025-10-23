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
    def parse_valor_monetario(valor_str: str) -> Optional[Decimal]:
        """Converte string monetária brasileira para Decimal"""
        if not valor_str or str(valor_str).strip() in ['', '-', '']:
            return None

        # Remove formatação brasileira (pontos como separadores de milhares, vírgula como decimal)
        valor_str = str(valor_str).strip()

        # Trata valores negativos (com hífen)
        negativo = False
        if valor_str.startswith('-'):
            negativo = True
            valor_str = valor_str[1:].strip()

        # Remove "R$", espaços e outros caracteres não numéricos exceto vírgula e ponto
        valor_str = re.sub(r'[R$\s]', '', valor_str)

        # Converte vírgula para ponto (formato brasileiro)
        valor_str = valor_str.replace('.', '').replace(',', '.')

        try:
            valor = Decimal(valor_str)
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
            df = pd.read_excel(BytesIO(file_content), sheet_name=0)

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

