"""add indexes for permissions and alugueis

Revision ID: add_indexes_permissions_alugueis
Revises: 
Create Date: 2025-10-26 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_indexes_permissions_alugueis'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Index for fast lookup of permissions by user
    op.create_index('ix_permissoes_financeiras_id_usuario', 'permissoes_financeiras', ['id_usuario'])
    op.create_index('ix_permissoes_financeiras_id_proprietario', 'permissoes_financeiras', ['id_proprietario'])
    # Indexes for alugueis_mensais filters and aggregates
    op.create_index('ix_alugueis_mensais_id_proprietario', 'alugueis_mensais', ['id_proprietario'])
    op.create_index('ix_alugueis_mensais_data_referencia', 'alugueis_mensais', ['data_referencia'])


def downgrade():
    op.drop_index('ix_alugueis_mensais_data_referencia', table_name='alugueis_mensais')
    op.drop_index('ix_alugueis_mensais_id_proprietario', table_name='alugueis_mensais')
    op.drop_index('ix_permissoes_financeiras_id_proprietario', table_name='permissoes_financeiras')
    op.drop_index('ix_permissoes_financeiras_id_usuario', table_name='permissoes_financeiras')
