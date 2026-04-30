"""add gap-fill SEO tables (cannibalization, internal links, orphans,
domain comparisons, bulk analysis, sitemap generations, robots validations,
schema templates, outreach campaigns + prospects, featured snippet watch,
PAA questions, SERP volatility events).

Revision ID: seo_extra_v1
Revises: advanced_seo_v1
Create Date: 2026-04-28
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'seo_extra_v1'
down_revision = 'advanced_seo_v1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "keyword_cannibalization",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("keyword", sa.String(512), nullable=False),
        sa.Column("urls", sa.JSON(), nullable=True),
        sa.Column("severity", sa.String(16), default="medium"),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "internal_links_graph",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_url", sa.String(2048), nullable=False),
        sa.Column("target_url", sa.String(2048), nullable=False),
        sa.Column("anchor_text", sa.Text(), nullable=True),
        sa.Column("is_nofollow", sa.Boolean(), default=False),
        sa.Column("link_position", sa.String(32), default="body"),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "orphan_pages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("in_sitemap", sa.Boolean(), default=False),
        sa.Column("page_authority", sa.Float(), default=0.0),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "domain_comparisons",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("primary_domain", sa.String(255), nullable=False),
        sa.Column("competitor_domains", sa.JSON(), nullable=True),
        sa.Column("metrics", sa.JSON(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "bulk_analysis_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_type", sa.String(32), default="onpage"),
        sa.Column("status", sa.String(16), default="queued"),
        sa.Column("total_urls", sa.Integer(), default=0),
        sa.Column("completed_urls", sa.Integer(), default=0),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "bulk_analysis_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bulk_analysis_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("status", sa.String(16), default="pending"),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
    )

    op.create_table(
        "sitemap_generations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url_count", sa.Integer(), default=0),
        sa.Column("file_url", sa.String(2048), nullable=True),
        sa.Column("xml_preview", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "robots_validations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("raw_content", sa.Text(), nullable=True),
        sa.Column("is_valid", sa.Boolean(), default=True),
        sa.Column("issues", sa.JSON(), nullable=True),
        sa.Column("rules", sa.JSON(), nullable=True),
        sa.Column("sitemap_directives", sa.JSON(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "schema_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("schema_type", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("inputs", sa.JSON(), nullable=True),
        sa.Column("json_ld", sa.JSON(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "outreach_campaigns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("goal", sa.Text(), nullable=True),
        sa.Column("status", sa.String(16), default="active"),
        sa.Column("target_link_count", sa.Integer(), default=0),
        sa.Column("won_link_count", sa.Integer(), default=0),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "outreach_prospects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("outreach_campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("contact_email", sa.String(255), nullable=True),
        sa.Column("contact_name", sa.String(255), nullable=True),
        sa.Column("status", sa.String(32), default="new"),
        sa.Column("last_contacted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("domain_authority", sa.Float(), default=0.0),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("won_link_url", sa.String(2048), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "featured_snippet_watch",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("keyword", sa.String(512), nullable=False),
        sa.Column("we_own", sa.Boolean(), default=False),
        sa.Column("current_owner_url", sa.String(2048), nullable=True),
        sa.Column("snippet_text", sa.Text(), nullable=True),
        sa.Column("snippet_type", sa.String(32), nullable=True),
        sa.Column("last_checked", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "paa_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("seed_keyword", sa.String(512), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer_url", sa.String(2048), nullable=True),
        sa.Column("answer_snippet", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "serp_volatility_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("keyword", sa.String(512), nullable=False),
        sa.Column("previous_position", sa.Integer(), nullable=True),
        sa.Column("current_position", sa.Integer(), nullable=True),
        sa.Column("delta", sa.Integer(), default=0),
        sa.Column("direction", sa.String(8), default="up"),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    for t in (
        "serp_volatility_events", "paa_questions", "featured_snippet_watch",
        "outreach_prospects", "outreach_campaigns",
        "schema_templates", "robots_validations", "sitemap_generations",
        "bulk_analysis_items", "bulk_analysis_jobs",
        "domain_comparisons", "orphan_pages", "internal_links_graph",
        "keyword_cannibalization",
    ):
        op.drop_table(t)
