from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal

# Schemas base
class UsuarioBase(BaseModel):
    username: str = Field(..., max_length=50)
    nome: str = Field(..., max_length=120)
    tipo: str = Field(..., pattern="^(administrador|usuario)$")
    email: str = Field(..., max_length=150)
    telefone: Optional[str] = Field(None, max_length=20)
    ativo: bool = True

class UsuarioCreate(BaseModel):
    nome: str = Field(..., max_length=120)
    tipo: str = Field(..., pattern="^(administrador|usuario)$")
    email: str = Field(..., max_length=150)
    telefone: Optional[str] = Field(None, max_length=20)
    ativo: bool = True

class UsuarioUpdate(BaseModel):
    nome: Optional[str] = Field(None, max_length=120)
    tipo: Optional[str] = Field(None, pattern="^(administrador|usuario)$")
    email: Optional[str] = Field(None, max_length=150)
    telefone: Optional[str] = Field(None, max_length=20)
    ativo: Optional[bool] = None

class Usuario(UsuarioBase):
    id: int

    class Config:
        from_attributes = True

# Schemas de Imóvel
class ImovelBase(BaseModel):
    nome: str = Field(..., max_length=120)
    endereco: str
    tipo: Optional[str] = Field(None, max_length=20)
    area_total: Optional[Decimal] = None
    area_construida: Optional[Decimal] = None
    valor_catastral: Optional[Decimal] = None
    valor_mercado: Optional[Decimal] = None
    iptu_anual: Optional[Decimal] = None
    condominio: Optional[Decimal] = None
    alugado: bool = False
    ativo: bool = True

class ImovelCreate(ImovelBase):
    pass

class ImovelUpdate(BaseModel):
    nome: Optional[str] = Field(None, max_length=120)
    endereco: Optional[str] = None
    tipo: Optional[str] = Field(None, max_length=20)
    area_total: Optional[Decimal] = None
    area_construida: Optional[Decimal] = None
    valor_catastral: Optional[Decimal] = None
    valor_mercado: Optional[Decimal] = None
    iptu_anual: Optional[Decimal] = None
    condominio: Optional[Decimal] = None
    alugado: Optional[bool] = None
    ativo: Optional[bool] = None

class Imovel(ImovelBase):
    id: int

    class Config:
        from_attributes = True

# Schemas de Participação
class ParticipacaoBase(BaseModel):
    id_imovel: int
    id_proprietario: int
    participacao: Decimal = Field(..., ge=0, le=100)
    data_cadastro: date

class ParticipacaoCreate(ParticipacaoBase):
    pass

class ParticipacaoUpdate(BaseModel):
    participacao: Optional[Decimal] = Field(None, ge=0, le=100)
    data_cadastro: Optional[date] = None

class Participacao(ParticipacaoBase):
    id: int

    class Config:
        from_attributes = True

# Schemas de Aluguel
class AluguelBase(BaseModel):
    id_imovel: int
    id_proprietario: int
    aluguel_liquido: Decimal = Field(default=0, ge=0, le=999999999.99)
    taxa_administracao_total: Decimal = Field(default=0, ge=0, le=999.99)
    darf: Decimal = Field(default=0, ge=0, le=999999999.99)
    data_cadastro: date

class AluguelCreate(AluguelBase):
    pass

class AluguelUpdate(BaseModel):
    aluguel_liquido: Optional[Decimal] = Field(None, ge=0, le=999999999.99)
    taxa_administracao_total: Optional[Decimal] = Field(None, ge=0, le=999.99)
    darf: Optional[Decimal] = Field(None, ge=0, le=999999999.99)
    data_cadastro: Optional[date] = None

class Aluguel(AluguelBase):
    id: int

    class Config:
        from_attributes = True

# Schemas de AluguelMensal
class AluguelMensalBase(BaseModel):
    id_imovel: int
    id_proprietario: int
    data_referencia: date
    valor_total: Decimal = Field(..., ge=0, le=999999999.99)
    valor_proprietario: Decimal = Field(..., ge=0, le=999999999.99)
    taxa_administracao: Decimal = Field(default=0, ge=0, le=999999999.99)
    status: Optional[str] = Field(None, max_length=20)

class AluguelMensalCreate(AluguelMensalBase):
    pass

class AluguelMensalUpdate(BaseModel):
    valor_total: Optional[Decimal] = Field(None, ge=0, le=999999999.99)
    valor_proprietario: Optional[Decimal] = Field(None, ge=0, le=999999999.99)
    taxa_administracao: Optional[Decimal] = Field(None, ge=0, le=999999999.99)
    status: Optional[str] = Field(None, max_length=20)

class AluguelMensal(AluguelMensalBase):
    id: int
    criado_em: Optional[datetime] = None
    atualizado_em: Optional[datetime] = None

    class Config:
        from_attributes = True

# Schemas de Alias
class AliasBase(BaseModel):
    nome: str = Field(..., max_length=120)
    ativo: bool = True

class AliasCreate(AliasBase):
    pass

class AliasUpdate(BaseModel):
    nome: Optional[str] = Field(None, max_length=120)
    ativo: Optional[bool] = None

class Alias(AliasBase):
    id: int

    class Config:
        from_attributes = True

# Schemas de AliasProprietario
class AliasProprietarioBase(BaseModel):
    id_alias: int
    id_proprietario: int

class AliasProprietarioCreate(AliasProprietarioBase):
    pass

class AliasProprietario(AliasProprietarioBase):
    class Config:
        from_attributes = True

# Schemas de Transferencia
class TransferenciaBase(BaseModel):
    id_alias: int
    id_proprietario: int
    valor: Decimal = Field(default=0, ge=0, le=999999999.99)
    data_inicio: date
    data_fim: Optional[date] = None

class TransferenciaCreate(TransferenciaBase):
    pass

class TransferenciaUpdate(BaseModel):
    valor: Optional[Decimal] = Field(None, ge=0, le=999999999.99)
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None

class Transferencia(TransferenciaBase):
    id: int

    class Config:
        from_attributes = True

# Schemas de PermissaoFinanceira
class PermissaoFinanceiraBase(BaseModel):
    id_usuario: int
    id_proprietario: int
    visualizar: bool = True
    editar: bool = False

class PermissaoFinanceiraCreate(PermissaoFinanceiraBase):
    pass

class PermissaoFinanceiraUpdate(BaseModel):
    visualizar: Optional[bool] = None
    editar: Optional[bool] = None

class PermissaoFinanceira(PermissaoFinanceiraBase):
    id: int
    data_criacao: date

    class Config:
        from_attributes = True

# Schemas de autenticação
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str