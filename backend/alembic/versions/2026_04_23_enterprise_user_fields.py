"""enterprise user fields

Revision ID: enterprise_user_v1
Revises: 
Create Date: 2026-04-23 11:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'enterprise_user_v1'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 1. Check and add is_superuser
    # Note: We use batch_alter_table for better compatibility if needed, 
    # but standard op.add_column is fine for Postgres.
    
    # We add columns only if they don't exist to avoid errors during the first automatic run
    # on servers where we already ran the manual ALTER commands.
    
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('users')]

    if 'is_superuser' not in columns:
        op.add_column('users', sa.Column('is_superuser', sa.Boolean(), server_default='false', nullable=False))
    
    if 'company_name' not in columns:
        op.add_column('users', sa.Column('company_name', sa.String(length=255), nullable=True))
        
    if 'avatar_url' not in columns:
        op.add_column('users', sa.Column('avatar_url', sa.String(length=1024), nullable=True))


def downgrade():
    op.drop_column('users', 'avatar_url')
    op.drop_column('users', 'company_name')
    op.drop_column('users', 'is_superuser')
