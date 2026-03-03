"""Add description, custo, markup, margem, grupo, subgrupo, marca, tax_group_id to products.

Revision ID: d4e5f6a7b8c9
Revises: c3e4f5a6b7d8
Create Date: 2026-03-02
"""

from alembic import op
import sqlalchemy as sa

revision = "d4e5f6a7b8c9"
down_revision = "c3e4f5a6b7d8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("products", sa.Column("description", sa.Text(), nullable=True))
    op.add_column(
        "products",
        sa.Column("custo", sa.Numeric(12, 2), nullable=True),
    )
    op.add_column(
        "products",
        sa.Column("markup", sa.Numeric(8, 2), nullable=True),
    )
    op.add_column(
        "products",
        sa.Column("margem", sa.Numeric(8, 2), nullable=True),
    )
    op.add_column(
        "products",
        sa.Column("grupo", sa.String(64), nullable=True),
    )
    op.add_column(
        "products",
        sa.Column("subgrupo", sa.String(64), nullable=True),
    )
    op.add_column(
        "products",
        sa.Column("marca", sa.String(64), nullable=True),
    )
    op.add_column(
        "products",
        sa.Column("tax_group_id", sa.String(36), nullable=True),
    )
    op.create_foreign_key(
        "fk_products_tax_group_id",
        "products",
        "tax_groups",
        ["tax_group_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_products_tax_group_id", "products", type_="foreignkey")
    op.drop_column("products", "tax_group_id")
    op.drop_column("products", "marca")
    op.drop_column("products", "subgrupo")
    op.drop_column("products", "grupo")
    op.drop_column("products", "margem")
    op.drop_column("products", "markup")
    op.drop_column("products", "custo")
    op.drop_column("products", "description")
