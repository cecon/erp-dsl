"""add product type and fuel fields

Revision ID: c3e4f5a6b7d8
Revises: b7f3a9c8d2e1
Create Date: 2026-03-02 21:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3e4f5a6b7d8'
down_revision: Union[str, None] = 'b7f3a9c8d2e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Product type enum ────────────────────────────────────────
    op.add_column(
        'products',
        sa.Column(
            'tipo_produto',
            sa.String(16),
            nullable=False,
            server_default='padrao',
        ),
    )

    # ── Fuel / ANP fields (all nullable) ─────────────────────────
    op.add_column('products', sa.Column('ind_comb', sa.String(2), nullable=True))
    op.add_column('products', sa.Column('cod_anp', sa.String(9), nullable=True))
    op.add_column('products', sa.Column('desc_anp', sa.String(95), nullable=True))
    op.add_column('products', sa.Column('uf_cons', sa.String(2), nullable=True))
    op.add_column('products', sa.Column('codif', sa.String(21), nullable=True))
    op.add_column('products', sa.Column('p_bio', sa.Numeric(6, 4), nullable=True))
    op.add_column('products', sa.Column('q_temp', sa.Numeric(16, 4), nullable=True))
    op.add_column('products', sa.Column('cst_is', sa.String(4), nullable=True))
    op.add_column('products', sa.Column('cclass_trib_is', sa.String(16), nullable=True))
    op.add_column('products', sa.Column('ad_rem_ibs', sa.Numeric(16, 4), nullable=True))
    op.add_column('products', sa.Column('ad_rem_cbs', sa.Numeric(16, 4), nullable=True))


def downgrade() -> None:
    op.drop_column('products', 'ad_rem_cbs')
    op.drop_column('products', 'ad_rem_ibs')
    op.drop_column('products', 'cclass_trib_is')
    op.drop_column('products', 'cst_is')
    op.drop_column('products', 'q_temp')
    op.drop_column('products', 'p_bio')
    op.drop_column('products', 'codif')
    op.drop_column('products', 'uf_cons')
    op.drop_column('products', 'desc_anp')
    op.drop_column('products', 'cod_anp')
    op.drop_column('products', 'ind_comb')
    op.drop_column('products', 'tipo_produto')
