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
                        nome=f"{nome} {sobrenome}".strip(),
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

            # Validar colunas obrigatórias
            colunas_esperadas = ['Nome', 'Endereço', 'Tipo']
            colunas_faltando = [col for col in colunas_esperadas if col not in df.columns]
            if colunas_faltando:
                return {
                    'success': False,
                    'message': f'Colunas obrigatórias faltando: {", ".join(colunas_faltando)}'
                }

            registros_importados = 0
            erros = []

            for idx, row in df.iterrows():
                try:
                    # Limpar e validar dados
                    nome = str(row['Nome']).strip()
                    endereco = str(row['Endereço']).strip()
                    tipo = str(row['Tipo']).strip()

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

                    # Parsear valores numéricos
                    area_total = self.parse_valor_monetario(str(row.get('Área Total', '')))
                    area_construida = self.parse_valor_monetario(str(row.get('Área Construída', '')))
                    valor_catastral = self.parse_valor_monetario(str(row.get('Valor Catastral', '')))
                    valor_mercado = self.parse_valor_monetario(str(row.get('Valor Mercado', '')))
                    iptu_anual = self.parse_valor_monetario(str(row.get('IPTU Anual', '')))
                    condominio = self.parse_valor_monetario(str(row.get('Condomínio', '')))

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

            # Verificar se tem coluna VALOR (pode ter espaço no final)
            coluna_valor = None
            for col in df.columns:
                if 'VALOR' in str(col).upper():
                    coluna_valor = col
                    break
            
            if not coluna_valor:
                return {
                    'success': False,
                    'message': 'Coluna VALOR é obrigatória'
                }

            registros_importados = 0
            erros = []

            for idx, row in df.iterrows():
                try:
                    nome_imovel = str(row.get('Nome', '')).strip()
                    endereco_imovel = str(row.get('Endereço', '')).strip()
                    valor_total = row[coluna_valor]

                    # Validar VALOR (deve ser próximo de 1.0 com tolerância)
                    if pd.isna(valor_total) or abs(float(valor_total) - 1.0) > 0.01:
                        erros.append(f"Linha {idx+2}: VALOR deve ser próximo de 1.0 (100%) - encontrado: {valor_total}")
                        continue

                    # Buscar imóvel
                    imovel = db.query(Imovel).filter(
                        Imovel.nome.ilike(f"%{nome_imovel}%"),
                        Imovel.endereco.ilike(f"%{endereco_imovel}%")
                    ).first()

                    if not imovel:
                        erros.append(f"Linha {idx+2}: Imóvel '{nome_imovel}' não encontrado")
                        continue

                    # Processar participações dos proprietários (colunas dinâmicas)
                    participacoes_imovel = []
                    soma_participacoes = Decimal('0')

                    for col_name in df.columns[3:]:  # Pular Nome, Endereço, VALOR
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
                            erros.append(f"Linha {idx+2}: Proprietário '{proprietario_nome}' não encontrado")
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

                    # Criar registros de participação
                    for part in participacoes_imovel:
                        participacao = Participacao(
                            id_imovel=imovel.id,
                            id_proprietario=part['proprietario'].id,
                            participacao=part['participacao'],
                            data_cadastro=date.today()
                        )
                        db.add(participacao)
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

    def importar_alugueis(self, file_content: bytes, db: Session) -> Dict[str, Any]:
        """Importa aluguéis mensais do Excel (múltiplas planilhas)"""
        try:
            # Carregar workbook para acessar múltiplas planilhas
            wb = openpyxl.load_workbook(BytesIO(file_content), data_only=True)

            registros_importados = 0
            erros = []
            meses_processados = 0

            # Processar cada planilha (cada uma representa um mês)
            for sheet_name in wb.sheetnames:
                try:
                    ws = wb[sheet_name]
                    meses_processados += 1

                    # Extrair data de referência da primeira célula (A1)
                    data_celula = ws['A1'].value
                    if not data_celula:
                        erros.append(f"Planilha '{sheet_name}': Data de referência não encontrada na célula A1")
                        continue

                    data_referencia = self.parse_data(str(data_celula))
                    if not data_referencia:
                        erros.append(f"Planilha '{sheet_name}': Data de referência inválida: {data_celula}")
                        continue

                    # Ler dados da planilha
                    rows = list(ws.iter_rows(values_only=True))
                    if len(rows) < 2:
                        erros.append(f"Planilha '{sheet_name}': Planilha deve ter pelo menos cabeçalho e uma linha de dados")
                        continue

                    # Cabeçalhos (linha 1, mas pular A1 que é a data)
                    headers = rows[0][1:]  # Pular primeira coluna (data)

                    # Processar cada linha de dados
                    for row_idx, row in enumerate(rows[1:], start=2):
                        try:
                            if not row or len(row) < 3:
                                continue  # Linha vazia

                            # Coluna 1: Nome/Endereço do imóvel
                            imovel_ident = str(row[0]).strip() if row[0] else ""
                            if not imovel_ident:
                                continue

                            # Coluna 2: Valor Total
                            valor_total = self.parse_valor_monetario(str(row[1]) if row[1] else "")
                            if valor_total is None or valor_total <= 0:
                                erros.append(f"Planilha '{sheet_name}', linha {row_idx}: Valor total inválido")
                                continue

                            # Última coluna: Taxa de Administração
                            taxa_admin = self.parse_valor_monetario(str(row[-1]) if row[-1] else "") or Decimal('0')

                            # Colunas do meio: Valores por proprietário
                            valores_proprietarios = []
                            soma_valores_proprietarios = Decimal('0')

                            for i, header in enumerate(headers[:-1]):  # Excluir última coluna (taxa)
                                if i + 2 >= len(row):  # +2 porque row[0] é imóvel, row[1] é valor total
                                    break

                                proprietario_nome = str(header).strip()
                                valor_str = str(row[i + 2]).strip() if row[i + 2] else ""

                                valor_proprietario = self.parse_valor_monetario(valor_str)
                                if valor_proprietario is None:
                                    valor_proprietario = Decimal('0')

                                if valor_proprietario > 0:
                                    valores_proprietarios.append({
                                        'nome': proprietario_nome,
                                        'valor': valor_proprietario
                                    })
                                    soma_valores_proprietarios += valor_proprietario

                            # Validar soma (valores proprietários + taxa ≈ valor total)
                            total_calculado = soma_valores_proprietarios + taxa_admin
                            if abs(total_calculado - valor_total) > Decimal('0.01'):  # Tolerância de 1 centavo
                                erros.append(f"Planilha '{sheet_name}', linha {row_idx}: Soma dos valores ({total_calculado}) não corresponde ao total ({valor_total})")
                                continue

                            # Buscar imóvel
                            imovel = db.query(Imovel).filter(
                                Imovel.nome.ilike(f"%{imovel_ident}%") |
                                Imovel.endereco.ilike(f"%{imovel_ident}%")
                            ).first()

                            if not imovel:
                                erros.append(f"Planilha '{sheet_name}', linha {row_idx}: Imóvel '{imovel_ident}' não encontrado")
                                continue

                            # Criar registros de aluguel mensal para cada proprietário
                            for vp in valores_proprietarios:
                                # Buscar proprietário
                                proprietario = db.query(Usuario).filter(
                                    Usuario.nome.ilike(f"%{vp['nome']}%")
                                ).first()

                                if not proprietario:
                                    erros.append(f"Planilha '{sheet_name}', linha {row_idx}: Proprietário '{vp['nome']}' não encontrado")
                                    continue

                                # Verificar se já existe registro para este mês/proprietário/imóvel
                                existente = db.query(AluguelMensal).filter(
                                    AluguelMensal.id_imovel == imovel.id,
                                    AluguelMensal.id_proprietario == proprietario.id,
                                    AluguelMensal.data_referencia == data_referencia
                                ).first()

                                if existente:
                                    # Atualizar existente
                                    existente.valor_total = valor_total
                                    existente.valor_proprietario = vp['valor']
                                    existente.taxa_administracao = taxa_admin
                                else:
                                    # Criar novo
                                    aluguel_mensal = AluguelMensal(
                                        id_imovel=imovel.id,
                                        id_proprietario=proprietario.id,
                                        data_referencia=data_referencia,
                                        valor_total=valor_total,
                                        valor_proprietario=vp['valor'],
                                        taxa_administracao=taxa_admin,
                                        status='recebido' if vp['valor'] > 0 else 'pendente'
                                    )
                                    db.add(aluguel_mensal)

                                registros_importados += 1

                        except Exception as e:
                            erros.append(f"Planilha '{sheet_name}', linha {row_idx}: Erro ao processar - {str(e)}")

                except Exception as e:
                    erros.append(f"Planilha '{sheet_name}': Erro ao processar planilha - {str(e)}")

            db.commit()

            return {
                'success': True,
                'message': f'Importação concluída. {registros_importados} registros de aluguel importados de {meses_processados} meses.',
                'registros_importados': registros_importados,
                'meses_processados': meses_processados,
                'erros': erros
            }

        except Exception as e:
            db.rollback()
            return {
                'success': False,
                'message': f'Erro na importação: {str(e)}'
            }
