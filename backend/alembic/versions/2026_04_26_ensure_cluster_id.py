"""ensure cluster_id and other missing columns

Revision ID: ensure_cluster_id_v2
Revises: fix_seo_suite_schema_v1
Create Date: 2026-04-26 07:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'ensure_cluster_id_v2'
down_revision = 'fix_seo_suite_schema_v1'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # --- 1. Keywords Table ---
    if 'keywords' in inspector.get_table_names():
        columns = [c['name'] for c in inspector.get_columns('keywords')]
        if 'cluster_id' not in columns:
            print("Adding cluster_id to keywords table...")
            op.add_column('keywords', sa.Column('cluster_id', postgresql.UUID(as_uuid=True), nullable=True))
            op.create_foreign_key('fk_keywords_cluster_id', 'keywords', 'clusters', ['cluster_id'], ['id'], ondelete='SET NULL')
            op.create_index(op.f('ix_keywords_cluster_id'), 'keywords', ['cluster_id'], unique=False)

    # --- 2. Backlinks Table ---
    if 'backlinks' in inspector.get_table_names():
        columns = [c['name'] for c in inspector.get_columns('backlinks')]
        if 'target_url' not in columns:
            print("Adding target_url to backlinks table...")
            op.add_column('backlinks', sa.Column('target_url', sa.String(length=2048), nullable=True))
        if 'anchor_text' not in columns:
            op.add_column('backlinks', sa.Column('anchor_text', sa.String(length=1024), nullable=True))
        if 'authority_score' not in columns:
            op.add_column('backlinks', sa.Column('authority_score', sa.Float(), nullable=False, server_default='0.0'))


def downgrade():
    # No-op for safety in this forced fix
    pass
