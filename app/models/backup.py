from sqlalchemy import Column, Integer, String, TIMESTAMP, func, Text
from app.core.database import Base

class Backup(Base):
    __tablename__ = "backups"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(50), nullable=False)  # 'completo', 'parcial', etc.
    arquivo = Column(String(255), nullable=False)  # caminho do arquivo
    tamanho = Column(Integer, nullable=False)  # tamanho em bytes
    descricao = Column(Text, nullable=True)
    data_criacao = Column(TIMESTAMP, default=func.now())