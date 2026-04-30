"""add advanced SEO tables (audit issues, crawled pages, CWV, schemas, anchors,
toxic backlinks, link intersect, keyword ideas, SERP overview, content briefs,
content optimizer, topic clusters, local citations, local rank grid, log events,
generated reports)

Revision ID: advanced_seo_v1
Revises: ensure_cluster_id_v2
Create Date: 2026-04-28
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'advanced_seo_v1'
down_revision = 'ensure_cluster_id_v2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # site_audit_issues
    op.create_table(
        "site_audit_issues",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("audit_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("resolved", sa.Boolean(), default=False),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_issues_project_severity", "site_audit_issues", ["project_id", "severity"])

    # crawled_pages
    op.create_table(
        "crawled_pages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("content_type", sa.String(128), nullable=True),
        sa.Column("title", sa.String(512), nullable=True),
        sa.Column("meta_description", sa.Text(), nullable=True),
        sa.Column("h1", sa.Text(), nullable=True),
        sa.Column("word_count", sa.Integer(), default=0),
        sa.Column("internal_links", sa.Integer(), default=0),
        sa.Column("external_links", sa.Integer(), default=0),
        sa.Column("images", sa.Integer(), default=0),
        sa.Column("images_missing_alt", sa.Integer(), default=0),
        sa.Column("canonical_url", sa.String(2048), nullable=True),
        sa.Column("is_indexable", sa.Boolean(), default=True),
        sa.Column("response_time_ms", sa.Integer(), nullable=True),
        sa.Column("page_size_bytes", sa.Integer(), nullable=True),
        sa.Column("depth", sa.Integer(), default=0),
        sa.Column("schema_types", sa.JSON(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )

    # core_web_vitals
    op.create_table(
        "core_web_vitals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("strategy", sa.String(16), default="mobile"),
        sa.Column("lcp_ms", sa.Float(), nullable=True),
        sa.Column("inp_ms", sa.Float(), nullable=True),
        sa.Column("cls", sa.Float(), nullable=True),
        sa.Column("fcp_ms", sa.Float(), nullable=True),
        sa.Column("ttfb_ms", sa.Float(), nullable=True),
        sa.Column("si_ms", sa.Float(), nullable=True),
        sa.Column("tbt_ms", sa.Float(), nullable=True),
        sa.Column("performance_score", sa.Integer(), nullable=True),
        sa.Column("seo_score", sa.Integer(), nullable=True),
        sa.Column("accessibility_score", sa.Integer(), nullable=True),
        sa.Column("best_practices_score", sa.Integer(), nullable=True),
        sa.Column("opportunities", sa.JSON(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )

    # schema_markup
    op.create_table(
        "schema_markup",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("schema_type", sa.String(128), nullable=False),
        sa.Column("raw_data", sa.JSON(), nullable=True),
        sa.Column("is_valid", sa.Boolean(), default=True),
        sa.Column("validation_errors", sa.JSON(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )

    # anchor_texts
    op.create_table(
        "anchor_texts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("anchor", sa.String(512), nullable=False),
        sa.Column("classification", sa.String(32), default="generic"),
        sa.Column("count", sa.Integer(), default=0),
        sa.Column("referring_domains", sa.Integer(), default=0),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )

    # toxic_backlinks
    op.create_table(
        "toxic_backlinks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("referring_domain", sa.String(255), nullable=False),
        sa.Column("target_url", sa.String(2048), nullable=True),
        sa.Column("spam_score", sa.Float(), default=0.0),
        sa.Column("reasons", sa.JSON(), nullable=True),
        sa.Column("disavowed", sa.Boolean(), default=False),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False),
    )

    # link_intersect
    op.create_table(
        "link_intersect",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("referring_domain", sa.String(255), nullable=False),
        sa.Column("competitor_count", sa.Integer(), default=0),
        sa.Column("competitors", sa.JSON(), nullable=True),
        sa.Column("domain_authority", sa.Float(), default=0.0),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False),
    )

    # keyword_ideas
    op.create_table(
        "keyword_ideas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("seed", sa.String(255), nullable=False),
        sa.Column("keyword", sa.String(512), nullable=False),
        sa.Column("match_type", sa.String(16), default="related"),
        sa.Column("intent", sa.String(32), default="informational"),
        sa.Column("volume", sa.Integer(), default=0),
        sa.Column("difficulty", sa.Integer(), default=0),
        sa.Column("cpc", sa.Float(), default=0.0),
        sa.Column("competition", sa.Float(), default=0.0),
        sa.Column("serp_features", sa.JSON(), nullable=True),
        sa.Column("parent_topic", sa.String(255), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )

    # serp_overview
    op.create_table(
        "serp_overview",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("keyword_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("keywords.id", ondelete="CASCADE"), nullable=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("keyword_text", sa.String(512), nullable=False),
        sa.Column("location", sa.String(64), default="us"),
        sa.Column("device", sa.String(16), default="desktop"),
        sa.Column("results", sa.JSON(), nullable=True),
        sa.Column("features_present", sa.JSON(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )

    # content_briefs
    op.create_table(
        "content_briefs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_keyword", sa.String(512), nullable=False),
        sa.Column("title_suggestions", sa.JSON(), nullable=True),
        sa.Column("h1", sa.Text(), nullable=True),
        sa.Column("outline", sa.JSON(), nullable=True),
        sa.Column("semantic_terms", sa.JSON(), nullable=True),
        sa.Column("questions_to_answer", sa.JSON(), nullable=True),
        sa.Column("target_word_count", sa.Integer(), default=1500),
        sa.Column("avg_competitor_words", sa.Integer(), default=0),
        sa.Column("competitors_analyzed", sa.JSON(), nullable=True),
        sa.Column("readability_target", sa.String(32), default="grade-8"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )

    # content_optimizer_scores
    op.create_table(
        "content_optimizer_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_keyword", sa.String(512), nullable=False),
        sa.Column("url", sa.String(2048), nullable=True),
        sa.Column("word_count", sa.Integer(), default=0),
        sa.Column("readability_score", sa.Float(), default=0.0),
        sa.Column("grade_level", sa.String(32), nullable=True),
        sa.Column("keyword_density", sa.Float(), default=0.0),
        sa.Column("headings_score", sa.Integer(), default=0),
        sa.Column("semantic_coverage", sa.Float(), default=0.0),
        sa.Column("overall_score", sa.Integer(), default=0),
        sa.Column("suggestions", sa.JSON(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )

    # topic_clusters
    op.create_table(
        "topic_clusters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("pillar_topic", sa.String(255), nullable=False),
        sa.Column("pillar_url", sa.String(2048), nullable=True),
        sa.Column("supporting_topics", sa.JSON(), nullable=True),
        sa.Column("total_volume", sa.Integer(), default=0),
        sa.Column("coverage_score", sa.Integer(), default=0),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )

    # local_citations
    op.create_table(
        "local_citations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("directory", sa.String(128), nullable=False),
        sa.Column("listing_url", sa.String(2048), nullable=True),
        sa.Column("business_name", sa.String(255), nullable=True),
        sa.Column("address", sa.String(512), nullable=True),
        sa.Column("phone", sa.String(64), nullable=True),
        sa.Column("website", sa.String(512), nullable=True),
        sa.Column("consistency_score", sa.Integer(), default=100),
        sa.Column("issues", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(32), default="active"),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False),
    )

    # local_rank_grid
    op.create_table(
        "local_rank_grid",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("keyword", sa.String(255), nullable=False),
        sa.Column("grid_lat", sa.Float(), nullable=False),
        sa.Column("grid_lng", sa.Float(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column("radius_km", sa.Float(), default=5.0),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )

    # log_events
    op.create_table(
        "log_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("bot", sa.String(64), default="googlebot"),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("status_code", sa.Integer(), default=200),
        sa.Column("hits", sa.Integer(), default=1),
        sa.Column("last_crawled", sa.DateTime(timezone=True), nullable=False),
    )

    # generated_reports
    op.create_table(
        "generated_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("report_type", sa.String(64), default="full_seo"),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("file_url", sa.String(2048), nullable=True),
        sa.Column("branding", sa.JSON(), nullable=True),
        sa.Column("summary", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(32), default="pending"),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    for table in (
        "generated_reports", "log_events", "local_rank_grid", "local_citations",
        "topic_clusters", "content_optimizer_scores", "content_briefs",
        "serp_overview", "keyword_ideas", "link_intersect", "toxic_backlinks",
        "anchor_texts", "schema_markup", "core_web_vitals", "crawled_pages",
        "site_audit_issues",
    ):
        op.drop_table(table)
