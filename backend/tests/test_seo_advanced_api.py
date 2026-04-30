"""
Integration tests for the /api/seo/* advanced endpoints in app/api/seo_advanced.py.

External calls (PSI, DDG, Google Suggest, etc.) are stubbed via the service
layer, so these tests run fully offline.
"""
from __future__ import annotations

import io
import uuid
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.user import User
from app.models.seo import Backlinks
from app.models.competitor import Competitor
from app.models.seo_advanced import (
    SiteAuditIssue,
    CrawledPage,
    CoreWebVitals,
    KeywordIdea,
    AnchorText,
    ToxicBacklink,
    LocalCitation,
    LogEvent,
    ContentBrief,
    TopicCluster,
)


# ---------------------------------------------------------------------------
# Helpers — seed rows
# ---------------------------------------------------------------------------
async def _seed_audit_issues(db: AsyncSession, project_id) -> None:
    db.add_all([
        SiteAuditIssue(
            project_id=project_id, url="https://x.com/a", category="on_page",
            severity="error", code="title-missing", message="No title",
            recommendation="Add one", details={}, discovered_at=datetime.now(timezone.utc),
        ),
        SiteAuditIssue(
            project_id=project_id, url="https://x.com/b", category="performance",
            severity="warning", code="slow-response", message="Slow",
            recommendation="Optimize", details={}, discovered_at=datetime.now(timezone.utc),
        ),
        SiteAuditIssue(
            project_id=project_id, url="https://x.com/c", category="performance",
            severity="notice", code="page-too-large", message="Big",
            details={}, discovered_at=datetime.now(timezone.utc),
        ),
    ])
    db.add(CrawledPage(
        project_id=project_id, url="https://x.com/a", status_code=200, title="Title",
        word_count=300, response_time_ms=120, page_size_bytes=50000,
        timestamp=datetime.now(timezone.utc),
    ))
    await db.commit()


# ===========================================================================
# Site audit endpoints
# ===========================================================================
class TestAuditSummary:
    @pytest.mark.asyncio
    async def test_summary_aggregates_severities(
        self, client: AsyncClient, db_session: AsyncSession,
        test_user: User, test_project: Project, auth_headers: dict,
    ):
        await _seed_audit_issues(db_session, test_project.id)
        resp = await client.get(
            f"/api/seo/projects/{test_project.id}/audit/summary",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_pages"] == 1
        assert data["errors"] == 1
        assert data["warnings"] == 1
        assert data["notices"] == 1
        assert data["total_issues"] == 3
        assert "score" in data
        assert "issues_by_category" in data

    @pytest.mark.asyncio
    async def test_summary_404_for_other_users_project(
        self, client: AsyncClient, db_session: AsyncSession,
        test_project: Project, second_auth_headers: dict,
    ):
        resp = await client.get(
            f"/api/seo/projects/{test_project.id}/audit/summary",
            headers=second_auth_headers,
        )
        assert resp.status_code == 404


class TestAuditIssues:
    @pytest.mark.asyncio
    async def test_list_issues_returns_seeded_rows(
        self, client: AsyncClient, db_session: AsyncSession,
        test_project: Project, auth_headers: dict,
    ):
        await _seed_audit_issues(db_session, test_project.id)
        resp = await client.get(
            f"/api/seo/projects/{test_project.id}/audit/issues",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        rows = resp.json()
        assert len(rows) == 3
        codes = {r["code"] for r in rows}
        assert "title-missing" in codes

    @pytest.mark.asyncio
    async def test_filter_by_severity(
        self, client: AsyncClient, db_session: AsyncSession,
        test_project: Project, auth_headers: dict,
    ):
        await _seed_audit_issues(db_session, test_project.id)
        resp = await client.get(
            f"/api/seo/projects/{test_project.id}/audit/issues?severity=error",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        rows = resp.json()
        assert all(r["severity"] == "error" for r in rows)
        assert len(rows) == 1

    @pytest.mark.asyncio
    async def test_filter_by_category(
        self, client: AsyncClient, db_session: AsyncSession,
        test_project: Project, auth_headers: dict,
    ):
        await _seed_audit_issues(db_session, test_project.id)
        resp = await client.get(
            f"/api/seo/projects/{test_project.id}/audit/issues?category=performance",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        rows = resp.json()
        assert len(rows) == 2
        assert all(r["category"] == "performance" for r in rows)


class TestRunSiteAudit:
    @pytest.mark.asyncio
    async def test_run_audit_persists_pages_and_issues(
        self, client: AsyncClient, db_session: AsyncSession,
        test_project: Project, auth_headers: dict, monkeypatch,
    ):
        from app.services.seo.site_crawler import CrawlResult, CrawledPageData, CrawlIssue

        async def fake_crawl(url, max_pages, max_depth):
            return CrawlResult(
                pages=[CrawledPageData(url=url, status_code=200, title="t", word_count=50)],
                issues=[CrawlIssue(url=url, category="on_page", severity="warning",
                                   code="title-too-short", message="short")],
                summary={"total_pages": 1, "total_issues": 1, "errors": 0, "warnings": 1, "notices": 0,
                         "avg_response_time_ms": 0, "score": 98, "issues_by_category": {"on_page": 1}},
            )

        monkeypatch.setattr("app.api.seo_advanced.crawl_site", fake_crawl, raising=False)
        # The router does the import inside the function — patch the module
        import app.services.seo.site_crawler as sc
        monkeypatch.setattr(sc, "crawl_site", fake_crawl)

        resp = await client.post(
            f"/api/seo/projects/{test_project.id}/audit/run",
            json={"url": "https://example.com", "max_pages": 5, "max_depth": 2},
            headers=auth_headers,
        )
        assert resp.status_code == 202, resp.text
        body = resp.json()
        assert body["status"] == "completed"
        assert body["summary"]["score"] == 98


# ===========================================================================
# Core Web Vitals
# ===========================================================================
class TestCWV:
    @pytest.mark.asyncio
    async def test_run_cwv_persists_row(
        self, client: AsyncClient, db_session: AsyncSession,
        test_project: Project, auth_headers: dict, monkeypatch,
    ):
        async def fake_psi(url, strategy="mobile", api_key=None):
            return {
                "url": url, "strategy": strategy,
                "lcp_ms": 2400, "inp_ms": 180, "cls": 0.05,
                "fcp_ms": 1700, "ttfb_ms": 250, "si_ms": 3000, "tbt_ms": 100,
                "performance_score": 85, "seo_score": 92,
                "accessibility_score": 80, "best_practices_score": 95,
                "opportunities": [],
            }
        import app.services.seo.core_web_vitals as cwv
        monkeypatch.setattr(cwv, "run_pagespeed", fake_psi)

        resp = await client.post(
            f"/api/seo/projects/{test_project.id}/cwv/run?url=https://x.com&strategy=mobile",
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["lcp_ms"] == 2400
        assert body["performance_score"] == 85

    @pytest.mark.asyncio
    async def test_list_cwv_history(
        self, client: AsyncClient, db_session: AsyncSession,
        test_project: Project, auth_headers: dict,
    ):
        db_session.add(CoreWebVitals(
            project_id=test_project.id, url="https://x.com", strategy="mobile",
            lcp_ms=2200, performance_score=80, timestamp=datetime.now(timezone.utc),
        ))
        await db_session.commit()
        resp = await client.get(
            f"/api/seo/projects/{test_project.id}/cwv",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        rows = resp.json()
        assert len(rows) == 1
        assert rows[0]["lcp_ms"] == 2200


# ===========================================================================
# Keyword Magic
# ===========================================================================
class TestKeywordMagic:
    @pytest.mark.asyncio
    async def test_keyword_magic_persists_ideas(
        self, client: AsyncClient, db_session: AsyncSession,
        test_project: Project, auth_headers: dict, monkeypatch,
    ):
        async def fake_generate(seed, location, include_questions, limit):
            return [
                {"seed": seed, "keyword": "what is seo", "match_type": "question",
                 "intent": "informational", "volume": 1500, "difficulty": 30,
                 "cpc": 0.5, "competition": 0.3, "serp_features": [], "parent_topic": "seo"},
                {"seed": seed, "keyword": "best seo tools", "match_type": "phrase",
                 "intent": "commercial", "volume": 4000, "difficulty": 60,
                 "cpc": 4.2, "competition": 0.6, "serp_features": [], "parent_topic": "best"},
            ]
        import app.services.seo.keyword_magic as km
        monkeypatch.setattr(km, "generate_ideas", fake_generate)

        resp = await client.post(
            f"/api/seo/projects/{test_project.id}/keyword-magic",
            json={"seed": "seo", "limit": 50, "include_questions": True, "location": "us"},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        rows = resp.json()
        assert len(rows) == 2

    @pytest.mark.asyncio
    async def test_list_ideas_with_match_type_filter(
        self, client: AsyncClient, db_session: AsyncSession,
        test_project: Project, auth_headers: dict,
    ):
        db_session.add_all([
            KeywordIdea(project_id=test_project.id, seed="seo", keyword="what is seo",
                        match_type="question", intent="informational", volume=1500,
                        difficulty=30, cpc=0.5, competition=0.3, serp_features=[],
                        parent_topic="seo", timestamp=datetime.now(timezone.utc)),
            KeywordIdea(project_id=test_project.id, seed="seo", keyword="best seo tools",
                        match_type="phrase", intent="commercial", volume=4000,
                        difficulty=60, cpc=4.2, competition=0.6, serp_features=[],
                        parent_topic="best", timestamp=datetime.now(timezone.utc)),
        ])
        await db_session.commit()

        resp = await client.get(
            f"/api/seo/projects/{test_project.id}/keyword-magic?match_type=question",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        rows = resp.json()
        assert len(rows) == 1
        assert rows[0]["match_type"] == "question"


# ===========================================================================
# Backlink intelligence
# ===========================================================================
class TestBacklinkIntel:
    @pytest.mark.asyncio
    async def test_anchor_distribution_refresh(
        self, client: AsyncClient, db_session: AsyncSession,
        test_project: Project, auth_headers: dict,
    ):
        # Seed some backlinks to compute against
        db_session.add_all([
            Backlinks(project_id=test_project.id, referring_domain="a.com",
                      target_url="https://x.com", anchor_text="click here",
                      timestamp=datetime.now(timezone.utc)),
            Backlinks(project_id=test_project.id, referring_domain="b.com",
                      target_url="https://x.com", anchor_text="click here",
                      timestamp=datetime.now(timezone.utc)),
        ])
        await db_session.commit()

        resp = await client.post(
            f"/api/seo/projects/{test_project.id}/backlinks/anchors/refresh",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

        list_resp = await client.get(
            f"/api/seo/projects/{test_project.id}/backlinks/anchors",
            headers=auth_headers,
        )
        rows = list_resp.json()
        # the "click here" anchor should now exist
        assert any(r["anchor"] == "click here" for r in rows)

    @pytest.mark.asyncio
    async def test_toxic_scan_filters_spammy(
        self, client: AsyncClient, db_session: AsyncSession,
        test_project: Project, auth_headers: dict,
    ):
        db_session.add_all([
            Backlinks(project_id=test_project.id, referring_domain="cheap-loans.xyz",
                      target_url="https://x.com", anchor_text="payday loan",
                      timestamp=datetime.now(timezone.utc)),
            Backlinks(project_id=test_project.id, referring_domain="wikipedia.org",
                      target_url="https://x.com", anchor_text="reference",
                      timestamp=datetime.now(timezone.utc)),
        ])
        await db_session.commit()

        resp = await client.post(
            f"/api/seo/projects/{test_project.id}/backlinks/toxic/scan",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["toxic_count"] >= 1

        list_resp = await client.get(
            f"/api/seo/projects/{test_project.id}/backlinks/toxic",
            headers=auth_headers,
        )
        rows = list_resp.json()
        assert any(r["referring_domain"] == "cheap-loans.xyz" for r in rows)

    @pytest.mark.asyncio
    async def test_disavow_marks_row(
        self, client: AsyncClient, db_session: AsyncSession,
        test_project: Project, auth_headers: dict,
    ):
        toxic = ToxicBacklink(
            project_id=test_project.id, referring_domain="bad.xyz",
            spam_score=80, reasons=["bad TLD"],
            discovered_at=datetime.now(timezone.utc),
        )
        db_session.add(toxic)
        await db_session.commit()
        await db_session.refresh(toxic)

        resp = await client.post(
            f"/api/seo/projects/{test_project.id}/backlinks/toxic/{toxic.id}/disavow",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "disavowed"

    @pytest.mark.asyncio
    async def test_disavow_export_returns_google_format(
        self, client: AsyncClient, db_session: AsyncSession,
        test_project: Project, auth_headers: dict,
    ):
        db_session.add(ToxicBacklink(
            project_id=test_project.id, referring_domain="bad.xyz",
            spam_score=80, reasons=[], disavowed=True,
            discovered_at=datetime.now(timezone.utc),
        ))
        await db_session.commit()

        resp = await client.get(
            f"/api/seo/projects/{test_project.id}/backlinks/disavow.txt",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "domain:bad.xyz" in body["content"]
        assert body["format"] == "google_disavow"


# ===========================================================================
# Content
# ===========================================================================
class TestContent:
    @pytest.mark.asyncio
    async def test_optimize_uses_latest_brief_terms(
        self, client: AsyncClient, db_session: AsyncSession,
        test_project: Project, auth_headers: dict,
    ):
        db_session.add(ContentBrief(
            project_id=test_project.id, target_keyword="email marketing",
            title_suggestions=[], outline=[], semantic_terms=["automation", "deliverability"],
            questions_to_answer=[], target_word_count=1000, avg_competitor_words=900,
            competitors_analyzed=[], timestamp=datetime.now(timezone.utc),
        ))
        await db_session.commit()

        content = "<h1>Email marketing guide</h1>" + ("<p>email marketing automation deliverability is great. " * 50) + "</p>"
        resp = await client.post(
            f"/api/seo/projects/{test_project.id}/content/optimize",
            json={"target_keyword": "email marketing", "content": content},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["target_keyword"] == "email marketing"
        assert body["semantic_coverage"] > 0
        assert 0 <= body["overall_score"] <= 100

    @pytest.mark.asyncio
    async def test_build_topic_cluster_filters_by_pillar(
        self, client: AsyncClient, db_session: AsyncSession,
        test_project: Project, auth_headers: dict,
    ):
        db_session.add_all([
            KeywordIdea(project_id=test_project.id, seed="email", keyword="email marketing tools",
                        match_type="phrase", intent="commercial", volume=3000, difficulty=50,
                        cpc=2.0, competition=0.5, serp_features=[], parent_topic="email",
                        timestamp=datetime.now(timezone.utc)),
            KeywordIdea(project_id=test_project.id, seed="email", keyword="facebook ads",
                        match_type="related", intent="commercial", volume=9000, difficulty=70,
                        cpc=4.0, competition=0.7, serp_features=[], parent_topic="facebook",
                        timestamp=datetime.now(timezone.utc)),
        ])
        await db_session.commit()

        resp = await client.post(
            f"/api/seo/projects/{test_project.id}/content/clusters/build?pillar_topic=email%20marketing",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["pillar_topic"] == "email marketing"
        topics = [t["topic"] for t in body["supporting_topics"]]
        assert "email marketing tools" in topics
        assert "facebook ads" not in topics


# ===========================================================================
# Local SEO
# ===========================================================================
class TestLocalSEO:
    @pytest.mark.asyncio
    async def test_consistency_summary_empty(
        self, client: AsyncClient, db_session: AsyncSession,
        test_project: Project, auth_headers: dict,
    ):
        resp = await client.get(
            f"/api/seo/projects/{test_project.id}/local/consistency",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["score"] == 0
        assert body["directories_listed"] == 0

    @pytest.mark.asyncio
    async def test_consistency_summary_with_citations(
        self, client: AsyncClient, db_session: AsyncSession,
        test_project: Project, auth_headers: dict,
    ):
        db_session.add(LocalCitation(
            project_id=test_project.id, directory="Yelp", consistency_score=90,
            issues=[], discovered_at=datetime.now(timezone.utc),
        ))
        await db_session.commit()

        resp = await client.get(
            f"/api/seo/projects/{test_project.id}/local/consistency",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["score"] == 90

    @pytest.mark.asyncio
    async def test_run_grid_creates_cells(
        self, client: AsyncClient, db_session: AsyncSession,
        test_project: Project, auth_headers: dict,
    ):
        resp = await client.post(
            f"/api/seo/projects/{test_project.id}/local/grid/run"
            f"?keyword=plumber&center_lat=40.7&center_lng=-74.0&radius_km=3&grid_size=3",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        rows = resp.json()
        assert len(rows) == 9


# ===========================================================================
# Logs
# ===========================================================================
class TestLogs:
    @pytest.mark.asyncio
    async def test_upload_log_file_parses_and_stores(
        self, client: AsyncClient, db_session: AsyncSession,
        test_project: Project, auth_headers: dict,
    ):
        log = (
            b'66.249.66.1 - - [28/Apr/2026:10:00:00 +0000] "GET /a HTTP/1.1" 200 100 "-" '
            b'"Mozilla/5.0 (compatible; Googlebot/2.1)"\n'
            b'66.249.66.2 - - [28/Apr/2026:10:00:01 +0000] "GET /b HTTP/1.1" 404 0 "-" '
            b'"Mozilla/5.0 (compatible; bingbot/2.0)"\n'
        )
        resp = await client.post(
            f"/api/seo/projects/{test_project.id}/logs/upload",
            files={"file": ("access.log", log, "text/plain")},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["summary"]["total_hits"] == 2
        assert body["rows"] == 2

        list_resp = await client.get(
            f"/api/seo/projects/{test_project.id}/logs",
            headers=auth_headers,
        )
        assert list_resp.status_code == 200
        rows = list_resp.json()
        assert len(rows) == 2


# ===========================================================================
# Reports
# ===========================================================================
class TestReports:
    @pytest.mark.asyncio
    async def test_generate_report_creates_row(
        self, client: AsyncClient, db_session: AsyncSession,
        test_project: Project, auth_headers: dict,
    ):
        resp = await client.post(
            f"/api/seo/projects/{test_project.id}/reports/generate",
            json={"report_type": "full_seo", "title": "April Report",
                  "branding": {"brand_name": "MyAgency", "primary_color": "#000"}},
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["title"] == "April Report"
        assert body["report_type"] == "full_seo"
        assert body["status"] == "ready"
        assert body["file_url"]

    @pytest.mark.asyncio
    async def test_list_reports_returns_history(
        self, client: AsyncClient, db_session: AsyncSession,
        test_user: User, test_project: Project, auth_headers: dict,
    ):
        from app.models.seo_advanced import GeneratedReport
        db_session.add(GeneratedReport(
            project_id=test_project.id, user_id=test_user.id,
            report_type="full_seo", title="Past Report", status="ready",
            timestamp=datetime.now(timezone.utc),
        ))
        await db_session.commit()

        resp = await client.get(
            f"/api/seo/projects/{test_project.id}/reports",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        rows = resp.json()
        assert any(r["title"] == "Past Report" for r in rows)


# ===========================================================================
# Hub overview
# ===========================================================================
class TestHubOverview:
    @pytest.mark.asyncio
    async def test_hub_overview_aggregates_counts(
        self, client: AsyncClient, db_session: AsyncSession,
        test_project: Project, auth_headers: dict,
    ):
        await _seed_audit_issues(db_session, test_project.id)
        db_session.add(KeywordIdea(
            project_id=test_project.id, seed="seo", keyword="seo audit",
            match_type="related", intent="informational", volume=1000,
            difficulty=30, cpc=0.5, competition=0.3, serp_features=[],
            parent_topic="seo", timestamp=datetime.now(timezone.utc),
        ))
        await db_session.commit()

        resp = await client.get(
            f"/api/seo/projects/{test_project.id}/hub-overview",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        for key in ("site_score", "pages_crawled", "errors", "warnings",
                    "keywords_tracked", "keyword_ideas", "backlinks", "referring_domains"):
            assert key in body
        assert body["pages_crawled"] >= 1
        assert body["errors"] == 1
        assert body["keyword_ideas"] == 1


# ===========================================================================
# Authorization — all endpoints must 401 without token
# ===========================================================================
class TestAuthorization:
    @pytest.mark.asyncio
    async def test_audit_summary_requires_auth(self, client: AsyncClient, test_project: Project):
        resp = await client.get(f"/api/seo/projects/{test_project.id}/audit/summary")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_keyword_magic_requires_auth(self, client: AsyncClient, test_project: Project):
        resp = await client.post(
            f"/api/seo/projects/{test_project.id}/keyword-magic",
            json={"seed": "seo"},
        )
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_hub_overview_requires_auth(self, client: AsyncClient, test_project: Project):
        resp = await client.get(f"/api/seo/projects/{test_project.id}/hub-overview")
        assert resp.status_code in (401, 403)
