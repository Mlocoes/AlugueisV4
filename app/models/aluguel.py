from sqlalchemy import Column, Integer, Numeric, Date, ForeignKey, TIMESTAMP, func, String
from app.core.database import Base

class Aluguel(Base):
    __tablename__ = "alugueis"

    id = Column(Integer, primary_key=True, index=True)
    id_imovel = Column(Integer, ForeignKey("imoveis.id", ondelete="CASCADE"), nullable=False)
    id_proprietario = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    aluguel_liquido = Column(Numeric(12, 2), default=0)
    taxa_administracao_total = Column(Numeric(6, 2), default=0)
    darf = Column(Numeric(12, 2), default=0)
    data_cadastro = Column(Date, nullable=False)


class AluguelMensal(Base):
    """Modelo para armazenar aluguéis mensais detalhados por proprietário"""
    __tablename__ = "alugueis_mensais"

    id = Column(Integer, primary_key=True, index=True)
    id_imovel = Column(Integer, ForeignKey("imoveis.id", ondelete="CASCADE"), nullable=False)
    id_proprietario = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    data_referencia = Column(Date, nullable=False)  # Mês/ano de referência
    valor_total = Column(Numeric(12, 2), nullable=False)  # Valor total do aluguel do imóvel
    valor_proprietario = Column(Numeric(12, 2), nullable=False)  # Valor que cabe ao proprietário
    taxa_administracao = Column(Numeric(10, 2), default=0)  # Taxa de administração
    status = Column(String(20), default='pendente')  # pendente, recebido, atrasado
    criado_em = Column(TIMESTAMP, server_default=func.now())
    atualizado_em = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())