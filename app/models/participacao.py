from sqlalchemy import Column, Integer, Numeric, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Participacao(Base):
    __tablename__ = "participacoes"

    id = Column(Integer, primary_key=True, index=True)
    id_imovel = Column(Integer, ForeignKey("imoveis.id", ondelete="CASCADE"), nullable=False)
    id_proprietario = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    participacao = Column(Numeric(6, 3), nullable=False)  # 0-100
    data_cadastro = Column(Date, nullable=False)