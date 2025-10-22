from sqlalchemy import Column, Integer, String, Boolean
from app.core.database import Base

class Alias(Base):
    __tablename__ = "alias"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(120), nullable=False)
    ativo = Column(Boolean, default=True)