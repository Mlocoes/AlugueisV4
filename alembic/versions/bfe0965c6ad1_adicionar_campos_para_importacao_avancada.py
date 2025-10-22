"""Adicionar campos para importacao avancada

Revision ID: bfe0965c6ad1
Revises: 89c3a04cb4d4
Create Date: 2024-10-22 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bfe0965c6ad1'
down_revision: Union[str, None] = '89c3a04cb4d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Adicionar colunas à tabela usuarios
    op.add_column('usuarios', sa.Column('sobrenome', sa.String(length=120), nullable=True))
    op.add_column('usuarios', sa.Column('documento', sa.String(length=20), nullable=True))
    op.add_column('usuarios', sa.Column('tipo_documento', sa.String(length=10), nullable=True))
    op.add_column('usuarios', sa.Column('endereco', sa.Text(), nullable=True))
    op.add_column('usuarios', sa.Column('username', sa.String(length=50), nullable=True))
    op.add_column('usuarios', sa.Column('hashed_password', sa.String(length=512), nullable=True))
    op.add_column('usuarios', sa.Column('criado_em', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True))
    op.add_column('usuarios', sa.Column('atualizado_em', sa.TIMESTAMP(), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=True))

    # Adicionar constraint única para documento
    op.create_unique_constraint('uq_usuarios_documento', 'usuarios', ['documento'])

    # Adicionar colunas à tabela imoveis
    op.add_column('imoveis', sa.Column('tipo', sa.String(length=20), nullable=True))
    op.add_column('imoveis', sa.Column('area_total', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('imoveis', sa.Column('area_construida', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('imoveis', sa.Column('valor_catastral', sa.Numeric(precision=15, scale=2), nullable=True))
    op.add_column('imoveis', sa.Column('valor_mercado', sa.Numeric(precision=15, scale=2), nullable=True))
    op.add_column('imoveis', sa.Column('iptu_anual', sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column('imoveis', sa.Column('condominio', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('imoveis', sa.Column('criado_em', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True))
    op.add_column('imoveis', sa.Column('atualizado_em', sa.TIMESTAMP(), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=True))

    # Criar tabela alugueis_mensais
    op.create_table('alugueis_mensais',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('id_imovel', sa.Integer(), nullable=False),
        sa.Column('id_proprietario', sa.Integer(), nullable=False),
        sa.Column('data_referencia', sa.Date(), nullable=False),
        sa.Column('valor_total', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('valor_proprietario', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('taxa_administracao', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('criado_em', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('atualizado_em', sa.TIMESTAMP(), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['id_imovel'], ['imoveis.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['id_proprietario'], ['usuarios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    # Remover tabela alugueis_mensais
    op.drop_table('alugueis_mensais')

    # Remover colunas de imoveis
    op.drop_column('imoveis', 'atualizado_em')
    op.drop_column('imoveis', 'criado_em')
    op.drop_column('imoveis', 'condominio')
    op.drop_column('imoveis', 'iptu_anual')
    op.drop_column('imoveis', 'valor_mercado')
    op.drop_column('imoveis', 'valor_catastral')
    op.drop_column('imoveis', 'area_construida')
    op.drop_column('imoveis', 'area_total')
    op.drop_column('imoveis', 'tipo')

    # Remover colunas de usuarios
    op.drop_constraint('uq_usuarios_documento', 'usuarios', type_='unique')
    op.drop_column('usuarios', 'atualizado_em')
    op.drop_column('usuarios', 'criado_em')
    op.drop_column('usuarios', 'hashed_password')
    op.drop_column('usuarios', 'username')
    op.drop_column('usuarios', 'endereco')
    op.drop_column('usuarios', 'tipo_documento')
    op.drop_column('usuarios', 'documento')
    op.drop_column('usuarios', 'sobrenome')