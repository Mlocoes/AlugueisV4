"""
Serviço de cálculos financeiros
Centraliza a lógica de cálculos de taxas, valores e totais
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Dict, Optional
from decimal import Decimal
from datetime import date

from app.models.aluguel import Aluguel
from app.models.participacao import Participacao
from app.models.imovel import Imovel
from app.models.usuario import Usuario


class AluguelService:
    """Serviço para cálculos relacionados a aluguéis"""
    
    @staticmethod
    def calcular_taxa_admin_proprietario(
        taxa_administracao_total: Decimal,
        participacao: Decimal
    ) -> Decimal:
        """
        Calcula a taxa de administração individual do proprietário
        
        Fórmula: taxa_admin_proprietario = taxa_admin_total * (participacao / 100)
        
        Args:
            taxa_administracao_total: Taxa total de administração
            participacao: Percentual de participação (0-100)
        
        Returns:
            Taxa de administração do proprietário
        """
        return taxa_administracao_total * (participacao / Decimal("100"))
    
    @staticmethod
    def calcular_valor_proprietario(
        aluguel_liquido: Decimal,
        participacao: Decimal
    ) -> Decimal:
        """
        Calcula o valor do aluguel proporcional à participação do proprietário
        
        Args:
            aluguel_liquido: Valor líquido do aluguel
            participacao: Percentual de participação (0-100)
        
        Returns:
            Valor proporcional do proprietário
        """
        return aluguel_liquido * (participacao / Decimal("100"))
    
    @staticmethod
    def obter_total_anual(
        db: Session,
        ano: int,
        id_proprietario: Optional[int] = None,
        id_imovel: Optional[int] = None
    ) -> Dict[str, Decimal]:
        """
        Calcula totais de aluguéis para um ano específico
        
        Args:
            db: Sessão do banco
            ano: Ano para calcular
            id_proprietario: Filtrar por proprietário (opcional)
            id_imovel: Filtrar por imóvel (opcional)
        
        Returns:
            Dict com totais (aluguel_liquido, taxa_admin, darf)
        """
        query = db.query(
            func.sum(Aluguel.aluguel_liquido).label('total_liquido'),
            func.sum(Aluguel.taxa_administracao_total).label('total_taxa'),
            func.sum(Aluguel.darf).label('total_darf')
        ).filter(
            func.extract('year', Aluguel.data_cadastro) == ano
        )
        
        if id_proprietario:
            query = query.filter(Aluguel.id_proprietario == id_proprietario)
        
        if id_imovel:
            query = query.filter(Aluguel.id_imovel == id_imovel)
        
        resultado = query.first()
        
        return {
            "ano": ano,
            "total_aluguel_liquido": float(resultado.total_liquido or 0),
            "total_taxa_administracao": float(resultado.total_taxa or 0),
            "total_darf": float(resultado.total_darf or 0),
            "total_geral": float(
                (resultado.total_liquido or 0) + 
                (resultado.total_taxa or 0) + 
                (resultado.total_darf or 0)
            )
        }
    
    @staticmethod
    def obter_total_mensal(
        db: Session,
        ano: int,
        mes: int,
        id_proprietario: Optional[int] = None,
        id_imovel: Optional[int] = None
    ) -> Dict[str, Decimal]:
        """
        Calcula totais de aluguéis para um mês específico
        
        Args:
            db: Sessão do banco
            ano: Ano
            mes: Mês (1-12)
            id_proprietario: Filtrar por proprietário (opcional)
            id_imovel: Filtrar por imóvel (opcional)
        
        Returns:
            Dict com totais mensais
        """
        query = db.query(
            func.sum(Aluguel.aluguel_liquido).label('total_liquido'),
            func.sum(Aluguel.taxa_administracao_total).label('total_taxa'),
            func.sum(Aluguel.darf).label('total_darf')
        ).filter(
            and_(
                func.extract('year', Aluguel.data_cadastro) == ano,
                func.extract('month', Aluguel.data_cadastro) == mes
            )
        )
        
        if id_proprietario:
            query = query.filter(Aluguel.id_proprietario == id_proprietario)
        
        if id_imovel:
            query = query.filter(Aluguel.id_imovel == id_imovel)
        
        resultado = query.first()
        
        return {
            "ano": ano,
            "mes": mes,
            "total_aluguel_liquido": float(resultado.total_liquido or 0),
            "total_taxa_administracao": float(resultado.total_taxa or 0),
            "total_darf": float(resultado.total_darf or 0),
            "total_geral": float(
                (resultado.total_liquido or 0) + 
                (resultado.total_taxa or 0) + 
                (resultado.total_darf or 0)
            )
        }
    
    @staticmethod
    def obter_relatorio_por_proprietario(
        db: Session,
        ano: int,
        mes: Optional[int] = None
    ) -> List[Dict]:
        """
        Gera relatório de aluguéis agrupado por proprietário
        
        Args:
            db: Sessão do banco
            ano: Ano para o relatório
            mes: Mês opcional (se None, considera o ano todo)
        
        Returns:
            Lista de dicts com dados por proprietário
        """
        query = db.query(
            Usuario.id,
            Usuario.nome,
            func.sum(Aluguel.aluguel_liquido).label('total_liquido'),
            func.sum(Aluguel.taxa_administracao_total).label('total_taxa'),
            func.sum(Aluguel.darf).label('total_darf'),
            func.count(Aluguel.id).label('num_alugueis')
        ).join(
            Aluguel, Aluguel.id_proprietario == Usuario.id
        ).filter(
            func.extract('year', Aluguel.data_cadastro) == ano
        )
        
        if mes:
            query = query.filter(func.extract('month', Aluguel.data_cadastro) == mes)
        
        query = query.group_by(Usuario.id, Usuario.nome)
        
        resultados = query.all()
        
        relatorio = []
        for r in resultados:
            relatorio.append({
                "id_proprietario": r.id,
                "nome_proprietario": r.nome,
                "total_aluguel_liquido": float(r.total_liquido or 0),
                "total_taxa_administracao": float(r.total_taxa or 0),
                "total_darf": float(r.total_darf or 0),
                "total_geral": float(
                    (r.total_liquido or 0) + 
                    (r.total_taxa or 0) + 
                    (r.total_darf or 0)
                ),
                "num_alugueis": r.num_alugueis
            })
        
        return relatorio
    
    @staticmethod
    def obter_relatorio_por_imovel(
        db: Session,
        ano: int,
        mes: Optional[int] = None
    ) -> List[Dict]:
        """
        Gera relatório de aluguéis agrupado por imóvel
        
        Args:
            db: Sessão do banco
            ano: Ano para o relatório
            mes: Mês opcional
        
        Returns:
            Lista de dicts com dados por imóvel
        """
        query = db.query(
            Imovel.id,
            Imovel.nome,
            Imovel.endereco,
            func.sum(Aluguel.aluguel_liquido).label('total_liquido'),
            func.sum(Aluguel.taxa_administracao_total).label('total_taxa'),
            func.sum(Aluguel.darf).label('total_darf'),
            func.count(Aluguel.id).label('num_registros')
        ).join(
            Aluguel, Aluguel.id_imovel == Imovel.id
        ).filter(
            func.extract('year', Aluguel.data_cadastro) == ano
        )
        
        if mes:
            query = query.filter(func.extract('month', Aluguel.data_cadastro) == mes)
        
        query = query.group_by(Imovel.id, Imovel.nome, Imovel.endereco)
        
        resultados = query.all()
        
        relatorio = []
        for r in resultados:
            relatorio.append({
                "id_imovel": r.id,
                "nome_imovel": r.nome,
                "endereco": r.endereco,
                "total_aluguel_liquido": float(r.total_liquido or 0),
                "total_taxa_administracao": float(r.total_taxa or 0),
                "total_darf": float(r.total_darf or 0),
                "total_geral": float(
                    (r.total_liquido or 0) + 
                    (r.total_taxa or 0) + 
                    (r.total_darf or 0)
                ),
                "num_registros": r.num_registros
            })
        
        return relatorio
