"""add fiscal catalog, agent models, and product fields

Revision ID: a1b2c3d4e5f6
Revises: ce9d21c95b88
Create Date: 2026-02-27 00:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'ce9d21c95b88'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Fiscal Catalog tables (shared, no tenant_id) ─────────────

    op.create_table(
        'ncm',
        sa.Column('codigo', sa.String(8), primary_key=True),
        sa.Column('descricao', sa.Text(), nullable=False),
        sa.Column('sujeito_is', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('cclass_trib_is', sa.String(16), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        'cest',
        sa.Column('codigo', sa.String(7), primary_key=True),
        sa.Column('descricao', sa.Text(), nullable=False),
        sa.Column('ncm_codigo', sa.String(8), nullable=False, index=True),
    )

    op.create_table(
        'classificacoes_tributarias',
        sa.Column('codigo', sa.String(16), primary_key=True),
        sa.Column('descricao', sa.Text(), nullable=False),
        sa.Column('cst_ibs_cbs', sa.String(4), nullable=False),
        sa.Column('regime', sa.String(32), nullable=False),
        sa.Column('permite_reducao', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('percentual_reducao', sa.Numeric(6, 2), nullable=True),
        sa.Column('exige_diferimento', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('exige_is', sa.Boolean(), nullable=False, server_default=sa.text('false')),
    )

    # ── Agent / AI tables ────────────────────────────────────────

    skill_type_enum = sa.Enum('builtin', 'custom', 'llm', 'http', name='skill_type_enum')
    chat_role_enum = sa.Enum('user', 'agent', 'skill', name='chat_role_enum')

    op.create_table(
        'llm_providers',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('provider', sa.String(64), nullable=False),
        sa.Column('model', sa.String(128), nullable=False),
        sa.Column('api_key_encrypted', sa.Text(), nullable=False),
        sa.Column('base_url', sa.Text(), nullable=True),
        sa.Column('params', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default=sa.text('1')),
    )

    op.create_table(
        'skills',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=True, index=True),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('skill_type', skill_type_enum, nullable=False, server_default='builtin'),
        sa.Column('implementation', sa.Text(), nullable=True),
        sa.Column('params_schema', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default=sa.text('1')),
    )

    op.create_table(
        'chat_sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('user_id', sa.String(36), nullable=False, index=True),
        sa.Column('context', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        'chat_messages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('session_id', sa.String(36), nullable=False, index=True),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('role', chat_role_enum, nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('skill_name', sa.String(128), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )

    # ── Expand products table ────────────────────────────────────

    op.add_column('products', sa.Column('ean', sa.String(14), nullable=True))
    op.add_column('products', sa.Column('foto_url', sa.Text(), nullable=True))
    op.add_column('products', sa.Column('descricao_tecnica', sa.Text(), nullable=True))
    op.add_column('products', sa.Column('unidade', sa.String(6), nullable=True, server_default='UN'))
    op.add_column('products', sa.Column('ncm_codigo', sa.String(8), nullable=True))
    op.add_column('products', sa.Column('cest_codigo', sa.String(7), nullable=True))
    op.add_column('products', sa.Column('cclass_codigo', sa.String(16), nullable=True))
    op.add_column('products', sa.Column('custom_fields', sa.JSON(), nullable=True))


def downgrade() -> None:
    # ── Remove product columns ───────────────────────────────────

    op.drop_column('products', 'custom_fields')
    op.drop_column('products', 'cclass_codigo')
    op.drop_column('products', 'cest_codigo')
    op.drop_column('products', 'ncm_codigo')
    op.drop_column('products', 'unidade')
    op.drop_column('products', 'descricao_tecnica')
    op.drop_column('products', 'foto_url')
    op.drop_column('products', 'ean')

    # ── Drop agent tables ────────────────────────────────────────

    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
    op.drop_table('skills')
    op.drop_table('llm_providers')

    sa.Enum(name='chat_role_enum').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='skill_type_enum').drop(op.get_bind(), checkfirst=True)

    # ── Drop fiscal catalog tables ───────────────────────────────

    op.drop_table('classificacoes_tributarias')
    op.drop_table('cest')
    op.drop_table('ncm')
