"""fix seo suite schema

Revision ID: fix_seo_suite_schema_v1
Revises: 07c0c267c611
Create Date: 2026-04-26 06:25:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'fix_seo_suite_schema_v1'
down_revision = '07c0c267c611'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # 1. backlinks
    if 'backlinks' not in tables:
        op.create_table(
            'backlinks',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('referring_domain', sa.String(length=255), nullable=False),
            sa.Column('target_url', sa.String(length=2048), nullable=True),
            sa.Column('anchor_text', sa.String(length=1024), nullable=True),
            sa.Column('status', sa.String(length=32), nullable=False, server_default='active'),
            sa.Column('authority_score', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('first_seen', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column('last_seen', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        )
        op.create_index(op.f('ix_backlinks_id'), 'backlinks', ['id'], unique=False)
        op.create_index(op.f('ix_backlinks_project_id'), 'backlinks', ['project_id'], unique=False)
        op.create_index(op.f('ix_backlinks_referring_domain'), 'backlinks', ['referring_domain'], unique=False)
        op.create_index(op.f('ix_backlinks_timestamp'), 'backlinks', ['timestamp'], unique=False)
    else:
        columns = [c['name'] for c in inspector.get_columns('backlinks')]
        if 'target_url' not in columns:
            op.add_column('backlinks', sa.Column('target_url', sa.String(length=2048), nullable=True))
        if 'anchor_text' not in columns:
            op.add_column('backlinks', sa.Column('anchor_text', sa.String(length=1024), nullable=True))
        if 'status' not in columns:
            op.add_column('backlinks', sa.Column('status', sa.String(length=32), nullable=False, server_default='active'))
        if 'authority_score' not in columns:
            op.add_column('backlinks', sa.Column('authority_score', sa.Float(), nullable=False, server_default='0.0'))
        if 'first_seen' not in columns:
            op.add_column('backlinks', sa.Column('first_seen', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
        if 'last_seen' not in columns:
            op.add_column('backlinks', sa.Column('last_seen', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
        if 'timestamp' not in columns:
            op.add_column('backlinks', sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
            op.create_index(op.f('ix_backlinks_timestamp'), 'backlinks', ['timestamp'], unique=False)

    # 2. rank_history
    if 'rank_history' not in tables:
        op.create_table(
            'rank_history',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('keyword_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('rank', sa.Integer(), nullable=True),
            sa.Column('search_volume', sa.Integer(), nullable=True),
            sa.Column('cpc', sa.Float(), nullable=True),
            sa.Column('device', sa.String(length=32), nullable=False, server_default='desktop'),
            sa.Column('location', sa.String(length=128), nullable=True),
            sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['keyword_id'], ['keywords.id'], ondelete='CASCADE'),
        )
        op.create_index(op.f('ix_rank_history_id'), 'rank_history', ['id'], unique=False)
        op.create_index(op.f('ix_rank_history_keyword_id'), 'rank_history', ['keyword_id'], unique=False)
        op.create_index(op.f('ix_rank_history_timestamp'), 'rank_history', ['timestamp'], unique=False)

    # 3. serp_features
    if 'serp_features' not in tables:
        op.create_table(
            'serp_features',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('keyword_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('featured_snippet', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('rich_snippets', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('ads', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('knowledge_panel', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['keyword_id'], ['keywords.id'], ondelete='CASCADE'),
            sa.UniqueConstraint('keyword_id')
        )
        op.create_index(op.f('ix_serp_features_id'), 'serp_features', ['id'], unique=False)
        op.create_index(op.f('ix_serp_features_keyword_id'), 'serp_features', ['keyword_id'], unique=False)
        op.create_index(op.f('ix_serp_features_timestamp'), 'serp_features', ['timestamp'], unique=False)

    # 4. competitor_keywords
    if 'competitor_keywords' not in tables:
        op.create_table(
            'competitor_keywords',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('competitor_domain', sa.String(length=255), nullable=False),
            sa.Column('keywords', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
            sa.Column('count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        )
        op.create_index(op.f('ix_competitor_keywords_competitor_domain'), 'competitor_keywords', ['competitor_domain'], unique=False)
        op.create_index(op.f('ix_competitor_keywords_id'), 'competitor_keywords', ['id'], unique=False)
        op.create_index(op.f('ix_competitor_keywords_project_id'), 'competitor_keywords', ['project_id'], unique=False)
        op.create_index(op.f('ix_competitor_keywords_timestamp'), 'competitor_keywords', ['timestamp'], unique=False)

    # 5. site_audit_history
    if 'site_audit_history' not in tables:
        op.create_table(
            'site_audit_history',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('url', sa.String(length=2048), nullable=False),
            sa.Column('score', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('total_errors', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('total_warnings', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('pages_crawled', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('crawl_depth', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        )
        op.create_index(op.f('ix_site_audit_history_id'), 'site_audit_history', ['id'], unique=False)
        op.create_index(op.f('ix_site_audit_history_project_id'), 'site_audit_history', ['project_id'], unique=False)
        op.create_index(op.f('ix_site_audit_history_timestamp'), 'site_audit_history', ['timestamp'], unique=False)


def downgrade():
    op.drop_table('site_audit_history')
    op.drop_table('competitor_keywords')
    op.drop_table('serp_features')
    op.drop_table('rank_history')
    op.drop_table('backlinks')
