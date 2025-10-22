from sqlalchemy import Column, Integer, Boolean, TIMESTAMP, func, ForeignKey
from app.core.database import Base

class PermissaoFinanceira(Base):
    __tablename__ = "permissoes_financeiras"

    id = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    id_proprietario = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    visualizar = Column(Boolean, default=True)
    editar = Column(Boolean, default=False)
    data_criacao = Column(TIMESTAMP, default=func.now())