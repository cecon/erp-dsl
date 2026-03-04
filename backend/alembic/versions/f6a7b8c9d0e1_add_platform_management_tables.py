"""add platform management tables

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-03-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Accounts
    op.create_table(
        'accounts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(256), nullable=False),
        sa.Column(
            'is_active', sa.Boolean(),
            nullable=False, server_default=sa.text('true'),
        ),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Plans
    op.create_table(
        'plans',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(64), nullable=False),
        sa.Column('slug', sa.String(32), nullable=False, unique=True),
        sa.Column(
            'price', sa.Numeric(10, 2),
            nullable=False, server_default=sa.text('0'),
        ),
        sa.Column(
            'enabled', sa.Boolean(),
            nullable=False, server_default=sa.text('true'),
        ),
        sa.Column(
            'features', sa.JSON(),
            nullable=False, server_default=sa.text("'{}'"),
        ),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Subscriptions
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column(
            'account_id', sa.String(36),
            sa.ForeignKey('accounts.id', ondelete='CASCADE'),
            nullable=False, index=True,
        ),
        sa.Column(
            'plan_id', sa.String(36),
            sa.ForeignKey('plans.id'),
            nullable=False,
        ),
        sa.Column(
            'status', sa.String(16),
            nullable=False, server_default=sa.text("'active'"),
        ),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Projects
    op.create_table(
        'projects',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column(
            'account_id', sa.String(36),
            sa.ForeignKey('accounts.id', ondelete='CASCADE'),
            nullable=False, index=True,
        ),
        sa.Column(
            'subscription_id', sa.String(36),
            sa.ForeignKey('subscriptions.id'),
            nullable=False,
        ),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(64), nullable=False),
        sa.Column(
            'status', sa.String(16),
            nullable=False, server_default=sa.text("'active'"),
        ),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            'account_id', 'slug', name='uq_project_account_slug',
        ),
    )

    # Project companies
    op.create_table(
        'project_companies',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column(
            'project_id', sa.String(36),
            sa.ForeignKey('projects.id', ondelete='CASCADE'),
            nullable=False, unique=True,
        ),
        sa.Column(
            'type', sa.String(2),
            nullable=False, server_default=sa.text("'pj'"),
        ),
        sa.Column('razao_social', sa.String(255), nullable=True),
        sa.Column('nome_fantasia', sa.String(255), nullable=True),
        sa.Column('cnpj_cpf', sa.String(18), nullable=True),
        sa.Column('ie', sa.String(20), nullable=True),
        sa.Column('im', sa.String(20), nullable=True),
        sa.Column(
            'endereco', sa.JSON(),
            nullable=True, server_default=sa.text("'{}'"),
        ),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Project apps
    op.create_table(
        'project_apps',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column(
            'project_id', sa.String(36),
            sa.ForeignKey('projects.id', ondelete='CASCADE'),
            nullable=False, index=True,
        ),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(64), nullable=False),
        sa.Column(
            'status', sa.String(16),
            nullable=False, server_default=sa.text("'active'"),
        ),
        sa.Column('llm_provider', sa.String(64), nullable=True),
        sa.Column('llm_model', sa.String(128), nullable=True),
        sa.Column('llm_api_key', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            'project_id', 'slug', name='uq_app_project_slug',
        ),
    )

    # Project databases
    op.create_table(
        'project_databases',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column(
            'app_id', sa.String(36),
            sa.ForeignKey('project_apps.id', ondelete='CASCADE'),
            nullable=False, unique=True,
        ),
        sa.Column('db_name', sa.String(128), nullable=False),
        sa.Column('db_host', sa.String(255), nullable=False),
        sa.Column(
            'db_port', sa.Integer(),
            nullable=False, server_default=sa.text('5432'),
        ),
        sa.Column('db_user', sa.String(128), nullable=False),
        sa.Column('db_password', sa.String(256), nullable=False),
        sa.Column(
            'status', sa.String(16),
            nullable=False, server_default=sa.text("'provisioning'"),
        ),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Tenant migrations tracker
    op.create_table(
        'tenant_migrations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column(
            'app_id', sa.String(36),
            sa.ForeignKey('project_apps.id', ondelete='CASCADE'),
            nullable=False, index=True,
        ),
        sa.Column('migration_name', sa.String(255), nullable=False),
        sa.Column('applied_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            'app_id', 'migration_name', name='uq_tenant_migration',
        ),
    )


def downgrade() -> None:
    op.drop_table('tenant_migrations')
    op.drop_table('project_databases')
    op.drop_table('project_apps')
    op.drop_table('project_companies')
    op.drop_table('projects')
    op.drop_table('subscriptions')
    op.drop_table('plans')
    op.drop_table('accounts')
