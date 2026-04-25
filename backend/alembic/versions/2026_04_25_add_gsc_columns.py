"""add gsc columns

Revision ID: add_gsc_integration
Revises: 215342b3abec
Create Date: 2026-04-25 07:05:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_gsc_integration'
down_revision = '215342b3abec'
branch_labels = None
depends_on = None


def upgrade():
    # Add columns to users table
    op.add_column('users', sa.Column('gsc_access_token', sa.String(length=1024), nullable=True))
    op.add_column('users', sa.Column('gsc_refresh_token', sa.String(length=1024), nullable=True))
    op.add_column('users', sa.Column('gsc_token_expiry', sa.DateTime(timezone=True), nullable=True))
    
    # Add columns to projects table
    op.add_column('projects', sa.Column('gsc_connected', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('projects', sa.Column('gsc_property_url', sa.String(length=512), nullable=True))


def downgrade():
    op.drop_column('projects', 'gsc_property_url')
    op.drop_column('projects', 'gsc_connected')
    op.drop_column('users', 'gsc_token_expiry')
    op.drop_column('users', 'gsc_refresh_token')
    op.drop_column('users', 'gsc_access_token')
