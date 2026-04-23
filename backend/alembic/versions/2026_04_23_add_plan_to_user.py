"""add plan to user

Revision ID: add_plan_to_user_v1
Revises: enterprise_user_v1
Create Date: 2026-04-23 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_plan_to_user_v1'
down_revision = 'enterprise_user_v1'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('users')]

    if 'plan' not in columns:
        op.add_column('users', sa.Column('plan', sa.String(length=50), server_default='free', nullable=False))


def downgrade():
    op.drop_column('users', 'plan')
