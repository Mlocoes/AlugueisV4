from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, func, Text
from app.core.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    nome = Column(String(120), nullable=False)
    sobrenome = Column(String(120))  # Novo campo
    tipo = Column(String(20), nullable=False)  # 'administrador' ou 'usuario'
    email = Column(String(150), unique=True, nullable=False)
    telefone = Column(String(20))
    documento = Column(String(20), unique=True)  # CPF/CNPJ limpo (sem formatação)
    tipo_documento = Column(String(10), default='CPF')  # CPF ou CNPJ
    endereco = Column(Text)  # Novo campo
    hashed_password = Column(String(512), nullable=False)
    ativo = Column(Boolean, default=True)
    criado_em = Column(TIMESTAMP, server_default=func.now())
    atualizado_em = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    @property
    def papel(self):
        """Alias para compatibilidade com frontend que usa 'papel'"""
        return self.tipo