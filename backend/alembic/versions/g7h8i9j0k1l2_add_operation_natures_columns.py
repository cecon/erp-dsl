"""Add operation_natures extended columns.

Revision ID: g7h8i9j0k1l2
Revises: a9b0c1d2e3f4
Create Date: 2026-03-15
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "g7h8i9j0k1l2"
down_revision = "a9b0c1d2e3f4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("operation_natures", sa.Column("codigo", sa.String(16), nullable=False, server_default=""))
    op.add_column("operation_natures", sa.Column("finalidade", sa.String(32), nullable=False, server_default="Revenda"))
    op.add_column("operation_natures", sa.Column("movimenta_estoque", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.add_column("operation_natures", sa.Column("gera_financeiro", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.add_column("operation_natures", sa.Column("gera_nfe", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("operation_natures", sa.Column("observacoes", sa.String(1000), nullable=True, server_default=""))


def downgrade() -> None:
    op.drop_column("operation_natures", "observacoes")
    op.drop_column("operation_natures", "gera_nfe")
    op.drop_column("operation_natures", "gera_financeiro")
    op.drop_column("operation_natures", "movimenta_estoque")
    op.drop_column("operation_natures", "finalidade")
    op.drop_column("operation_natures", "codigo")
