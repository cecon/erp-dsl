"""initial_schema

Revision ID: ce9d21c95b88
Revises:
Create Date: 2026-02-27 02:07:40.414289

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ce9d21c95b88'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Tenants ──────────────────────────────────────────────────
    op.create_table(
        'tenants',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(64), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )

    # ── Users ────────────────────────────────────────────────────
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('username', sa.String(128), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(256), nullable=False),
        sa.Column('role', sa.String(32), server_default='user'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )

    # ── Page Versions ────────────────────────────────────────────
    page_scope_enum = sa.Enum('global', 'tenant', name='page_scope')
    version_status_enum = sa.Enum('draft', 'published', 'archived', name='version_status')

    op.create_table(
        'page_versions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('page_key', sa.String(64), nullable=False, index=True),
        sa.Column('scope', page_scope_enum, nullable=False, server_default='global'),
        sa.Column('tenant_id', sa.String(36), nullable=True, index=True),
        sa.Column('base_version_id', sa.String(36), nullable=True),
        sa.Column('version_number', sa.Integer(), nullable=False, server_default=sa.text('1')),
        sa.Column('schema_json', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('status', version_status_enum, nullable=False, server_default='draft'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            'page_key', 'scope', 'tenant_id', 'version_number',
            name='uq_page_version',
        ),
    )

    # ── Products (base fields only) ──────────────────────────────
    op.create_table(
        'products',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('price', sa.Numeric(12, 2), nullable=False, server_default=sa.text('0')),
        sa.Column('sku', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default=sa.text('1')),
    )

    # ── Audit Logs ───────────────────────────────────────────────
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('entity_type', sa.String(64), nullable=False),
        sa.Column('entity_id', sa.String(36), nullable=False),
        sa.Column('action', sa.String(32), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default=sa.text('1')),
    )

    # ── Tax Groups ───────────────────────────────────────────────
    op.create_table(
        'tax_groups',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('descricao', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default=sa.text('1')),
    )

    # ── Operation Natures ────────────────────────────────────────
    op.create_table(
        'operation_natures',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('descricao', sa.String(255), nullable=False),
        sa.Column('tipo_movimento', sa.String(16), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default=sa.text('1')),
    )

    # ── Fiscal Rules ─────────────────────────────────────────────
    op.create_table(
        'fiscal_rules',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('id_grupo_tributario', sa.String(36), nullable=False, index=True),
        sa.Column('id_natureza_operacao', sa.String(36), nullable=False, index=True),
        sa.Column('uf_origem', sa.String(2), nullable=False, server_default=''),
        sa.Column('uf_destino', sa.String(2), nullable=False, server_default=''),
        sa.Column('tipo_contribuinte_dest', sa.String(32), nullable=False, server_default=''),
        sa.Column('cfop', sa.String(8), nullable=False, server_default=''),
        sa.Column('icms_cst', sa.String(4), nullable=False, server_default=''),
        sa.Column('icms_csosn', sa.String(4), nullable=False, server_default=''),
        sa.Column('icms_aliquota', sa.Numeric(6, 2), nullable=False, server_default=sa.text('0')),
        sa.Column('icms_perc_reducao_bc', sa.Numeric(6, 2), nullable=False, server_default=sa.text('0')),
        sa.Column('pis_cst', sa.String(4), nullable=False, server_default=''),
        sa.Column('cofins_cst', sa.String(4), nullable=False, server_default=''),
        sa.Column('ibs_cbs_cst', sa.String(4), nullable=False, server_default=''),
        sa.Column('ibs_aliquota_uf', sa.Numeric(6, 2), nullable=False, server_default=sa.text('0')),
        sa.Column('ibs_aliquota_mun', sa.Numeric(6, 2), nullable=False, server_default=sa.text('0')),
        sa.Column('cbs_aliquota', sa.Numeric(6, 2), nullable=False, server_default=sa.text('0')),
        sa.Column('is_cst', sa.String(4), nullable=False, server_default=''),
        sa.Column('is_aliquota', sa.Numeric(6, 2), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default=sa.text('1')),
    )


def downgrade() -> None:
    op.drop_table('fiscal_rules')
    op.drop_table('operation_natures')
    op.drop_table('tax_groups')
    op.drop_table('audit_logs')
    op.drop_table('products')
    op.drop_table('page_versions')
    op.drop_table('users')
    op.drop_table('tenants')

    sa.Enum(name='version_status').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='page_scope').drop(op.get_bind(), checkfirst=True)
