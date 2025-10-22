"""
Serviço de validação de participações
Centraliza a lógica de negócio para validar participações de imóveis
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Optional
from decimal import Decimal
from fastapi import HTTPException

from app.models.participacao import Participacao
from app.models.imovel import Imovel


class ParticipacaoService:
    """Serviço para gerenciar lógica de negócio de participações"""
    
    TOLERANCIA = Decimal("0.4")  # Tolerância de 0.4% para soma de participações
    TOTAL_ESPERADO = Decimal("100.0")
    
    @staticmethod
    def validar_soma_participacoes(
        db: Session,
        id_imovel: int,
        data_cadastro: str,
        participacao_atual_id: Optional[int] = None
    ) -> Dict[str, any]:
        """
        Valida se a soma das participações de um imóvel é 100% (± 0.4%)
        
        Args:
            db: Sessão do banco de dados
            id_imovel: ID do imóvel a validar
            data_cadastro: Data de cadastro das participações
            participacao_atual_id: ID da participação sendo editada (para excluir do cálculo)
        
        Returns:
            Dict com resultado da validação e detalhes
        
        Raises:
            HTTPException: Se a soma não estiver dentro da tolerância
        """
        # Buscar todas as participações do imóvel na data especificada
        query = db.query(Participacao).filter(
            Participacao.id_imovel == id_imovel,
            Participacao.data_cadastro == data_cadastro
        )
        
        # Excluir participação atual se estiver editando
        if participacao_atual_id:
            query = query.filter(Participacao.id != participacao_atual_id)
        
        participacoes = query.all()
        
        # Calcular soma total
        soma_total = sum(p.participacao for p in participacoes)
        
        # Verificar se está dentro da tolerância
        diferenca = abs(soma_total - ParticipacaoService.TOTAL_ESPERADO)
        dentro_tolerancia = diferenca <= ParticipacaoService.TOLERANCIA
        
        resultado = {
            "valido": dentro_tolerancia,
            "soma_atual": float(soma_total),
            "diferenca": float(diferenca),
            "tolerancia": float(ParticipacaoService.TOLERANCIA),
            "total_esperado": float(ParticipacaoService.TOTAL_ESPERADO),
            "num_participacoes": len(participacoes),
            "mensagem": ""
        }
        
        if not dentro_tolerancia:
            if soma_total > ParticipacaoService.TOTAL_ESPERADO:
                resultado["mensagem"] = (
                    f"Soma das participações ({soma_total}%) excede 100%. "
                    f"Diferença: +{diferenca}% (tolerância: ±{ParticipacaoService.TOLERANCIA}%)"
                )
            else:
                resultado["mensagem"] = (
                    f"Soma das participações ({soma_total}%) é menor que 100%. "
                    f"Faltam: {diferenca}% (tolerância: ±{ParticipacaoService.TOLERANCIA}%)"
                )
        else:
            resultado["mensagem"] = f"Soma válida: {soma_total}% (dentro da tolerância)"
        
        return resultado
    
    @staticmethod
    def validar_antes_criar(
        db: Session,
        id_imovel: int,
        participacao: Decimal,
        data_cadastro: str
    ) -> None:
        """
        Valida se é possível adicionar uma nova participação
        
        Args:
            db: Sessão do banco
            id_imovel: ID do imóvel
            participacao: Percentual da nova participação
            data_cadastro: Data de cadastro
        
        Raises:
            HTTPException: Se adicionar tornaria a soma inválida
        """
        # Buscar participações existentes
        participacoes_existentes = db.query(Participacao).filter(
            Participacao.id_imovel == id_imovel,
            Participacao.data_cadastro == data_cadastro
        ).all()
        
        soma_atual = sum(p.participacao for p in participacoes_existentes)
        soma_com_nova = soma_atual + participacao
        
        diferenca = abs(soma_com_nova - ParticipacaoService.TOTAL_ESPERADO)
        
        if diferenca > ParticipacaoService.TOLERANCIA:
            raise HTTPException(
                status_code=400,
                detail={
                    "erro": "Soma de participações inválida",
                    "soma_atual": float(soma_atual),
                    "nova_participacao": float(participacao),
                    "soma_resultante": float(soma_com_nova),
                    "diferenca": float(diferenca),
                    "tolerancia": float(ParticipacaoService.TOLERANCIA),
                    "mensagem": (
                        f"Adicionar {participacao}% resultaria em {soma_com_nova}%, "
                        f"ultrapassando a tolerância de ±{ParticipacaoService.TOLERANCIA}%"
                    )
                }
            )
    
    @staticmethod
    def validar_antes_atualizar(
        db: Session,
        participacao_id: int,
        id_imovel: int,
        nova_participacao: Decimal,
        data_cadastro: str
    ) -> None:
        """
        Valida se é possível atualizar uma participação existente
        
        Args:
            db: Sessão do banco
            participacao_id: ID da participação sendo atualizada
            id_imovel: ID do imóvel
            nova_participacao: Novo percentual
            data_cadastro: Data de cadastro
        
        Raises:
            HTTPException: Se atualizar tornaria a soma inválida
        """
        # Buscar participações, exceto a atual
        outras_participacoes = db.query(Participacao).filter(
            Participacao.id_imovel == id_imovel,
            Participacao.data_cadastro == data_cadastro,
            Participacao.id != participacao_id
        ).all()
        
        soma_outras = sum(p.participacao for p in outras_participacoes)
        soma_com_atualizada = soma_outras + nova_participacao
        
        diferenca = abs(soma_com_atualizada - ParticipacaoService.TOTAL_ESPERADO)
        
        if diferenca > ParticipacaoService.TOLERANCIA:
            raise HTTPException(
                status_code=400,
                detail={
                    "erro": "Soma de participações inválida",
                    "soma_outras": float(soma_outras),
                    "nova_participacao": float(nova_participacao),
                    "soma_resultante": float(soma_com_atualizada),
                    "diferenca": float(diferenca),
                    "tolerancia": float(ParticipacaoService.TOLERANCIA),
                    "mensagem": (
                        f"Atualizar para {nova_participacao}% resultaria em {soma_com_atualizada}%, "
                        f"ultrapassando a tolerância de ±{ParticipacaoService.TOLERANCIA}%"
                    )
                }
            )
    
    @staticmethod
    def obter_participacoes_por_imovel(
        db: Session,
        id_imovel: int,
        data_cadastro: Optional[str] = None
    ) -> List[Dict]:
        """
        Obtém todas as participações de um imóvel, opcionalmente filtradas por data
        
        Args:
            db: Sessão do banco
            id_imovel: ID do imóvel
            data_cadastro: Data opcional para filtrar
        
        Returns:
            Lista de participações com informações do proprietário
        """
        query = db.query(Participacao).filter(Participacao.id_imovel == id_imovel)
        
        if data_cadastro:
            query = query.filter(Participacao.data_cadastro == data_cadastro)
        
        participacoes = query.all()
        
        resultado = []
        for p in participacoes:
            resultado.append({
                "id": p.id,
                "id_imovel": p.id_imovel,
                "id_proprietario": p.id_proprietario,
                "participacao": float(p.participacao),
                "data_cadastro": str(p.data_cadastro)
            })
        
        return resultado
    
    @staticmethod
    def obter_datas_disponiveis(db: Session, id_imovel: int) -> List[str]:
        """
        Obtém todas as datas de cadastro disponíveis para um imóvel
        
        Args:
            db: Sessão do banco
            id_imovel: ID do imóvel
        
        Returns:
            Lista de datas únicas ordenadas
        """
        datas = db.query(Participacao.data_cadastro).filter(
            Participacao.id_imovel == id_imovel
        ).distinct().order_by(Participacao.data_cadastro.desc()).all()
        
        return [str(d[0]) for d in datas]
