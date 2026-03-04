"""add skills table

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-03-03 23:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop old 'skills' table created by a1b2c3d4e5f6 with different schema
    op.execute('DROP TABLE IF EXISTS skills')
    op.create_table(
        'skills',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('name', sa.String(64), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('params_schema', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column(
            'category', sa.String(32),
            nullable=False, server_default='general',
        ),
        sa.Column(
            'enabled', sa.Boolean(),
            nullable=False, server_default=sa.text('true'),
        ),
        sa.Column(
            'version', sa.Integer(),
            nullable=False, server_default=sa.text('1'),
        ),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), nullable=True,
        ),
        sa.Column(
            'updated_at', sa.DateTime(timezone=True), nullable=True,
        ),
        sa.UniqueConstraint(
            'tenant_id', 'name', name='uq_skill_tenant_name',
        ),
    )


def downgrade() -> None:
    op.drop_table('skills')
