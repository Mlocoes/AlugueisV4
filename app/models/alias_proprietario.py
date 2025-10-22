from sqlalchemy import Column, Integer, ForeignKey
from app.core.database import Base

class AliasProprietario(Base):
    __tablename__ = "alias_proprietarios"

    id_alias = Column(Integer, ForeignKey("alias.id", ondelete="CASCADE"), primary_key=True)
    id_proprietario = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True)