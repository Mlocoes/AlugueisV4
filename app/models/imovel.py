from sqlalchemy import Column, Integer, String, Text, Boolean, Numeric
from app.core.database import Base

class Imovel(Base):
    __tablename__ = "imoveis"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(120), nullable=False)
    endereco = Column(Text, nullable=False)
    tipo = Column(String(20), nullable=False)  # 'Comercial' ou 'Residencial'
    area_total = Column(Numeric(10, 2))  # Área total em m²
    area_construida = Column(Numeric(10, 2))  # Área construída em m²
    valor_catastral = Column(Numeric(15, 2))  # Valor catastral
    valor_mercado = Column(Numeric(15, 2))  # Valor de mercado
    iptu_anual = Column(Numeric(12, 2))  # IPTU anual
    condominio = Column(Numeric(10, 2))  # Valor do condomínio
    alugado = Column(Boolean, default=False)
    ativo = Column(Boolean, default=True)