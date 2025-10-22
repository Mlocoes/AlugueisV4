from sqlalchemy import Column, Integer, Numeric, Date, ForeignKey
from app.core.database import Base

class Transferencia(Base):
    __tablename__ = "transferencias"

    id = Column(Integer, primary_key=True, index=True)
    id_alias = Column(Integer, ForeignKey("alias.id", ondelete="CASCADE"), nullable=False)
    id_proprietario = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    valor = Column(Numeric(12, 2), default=0)
    data_inicio = Column(Date, nullable=False)
    data_fim = Column(Date)