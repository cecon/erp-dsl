"""add workflows table

Revision ID: b7f3a9c8d2e1
Revises: a1b2c3d4e5f6
Create Date: 2026-03-01 00:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7f3a9c8d2e1'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'workflows',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('command', sa.String(64), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('steps', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column(
            'status', sa.String(16),
            nullable=False, server_default='draft',
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
            'tenant_id', 'command', name='uq_workflow_tenant_command',
        ),
    )


def downgrade() -> None:
    op.drop_table('workflows')
