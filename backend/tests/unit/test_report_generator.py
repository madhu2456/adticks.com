"""Unit tests for app.services.seo.report_generator."""
from __future__ import annotations

import os
import pytest

from app.services.seo.report_generator import (
    build_markdown_report,
    build_pdf_report,
)


SAMPLE_SUMMARY = {
    "site_score": 78,
    "pages_crawled": 42,
    "total_issues": 17,
    "errors": 3,
    "warnings": 9,
    "backlinks": 1240,
    "referring_domains": 156,
    "keywords_tracked": 89,
    "top10_keywords": 12,
    "cwv_score": 81,
    "new_links_30d": 14,
    "lost_links_30d": 5,
    "toxic_domains": 2,
    "top_issues": [
        {"severity": "error", "message": "Title missing", "url": "/about"},
        {"severity": "warning", "message": "Slow response", "url": "/products"},
    ],
    "top_keywords": [
        {"keyword": "running shoes", "volume": 5000, "difficulty": 60, "position": 7},
        {"keyword": "best shoes", "volume": 3000, "difficulty": 50, "position": None},
    ],
}


class TestMarkdown:
    def test_includes_brand_and_project(self):
        md = build_markdown_report("Adticks", SAMPLE_SUMMARY, {"brand_name": "MyAgency"})
        assert "MyAgency" in md
        assert "Adticks" in md

    def test_executive_summary_metrics_present(self):
        md = build_markdown_report("Project X", SAMPLE_SUMMARY)
        for token in ["78/100", "42", "17", "1240", "156", "89"]:
            assert token in md

    def test_top_issues_rendered(self):
        md = build_markdown_report("Project X", SAMPLE_SUMMARY)
        assert "Title missing" in md
        assert "[ERROR]" in md
        assert "[WARNING]" in md

    def test_keywords_table_rendered(self):
        md = build_markdown_report("Project X", SAMPLE_SUMMARY)
        assert "running shoes" in md
        # Markdown table separator
        assert "|---|" in md or "| ---" in md or "|---" in md


class TestPDF:
    def test_pdf_or_md_fallback_returned(self, tmp_path):
        out_path = str(tmp_path / "report.pdf")
        actual = build_pdf_report("Adticks", SAMPLE_SUMMARY, out_path, {"brand_name": "MyAgency"})
        # Either a real PDF was made or it fell back to .md
        assert actual.endswith(".pdf") or actual.endswith(".md")
        assert os.path.exists(actual)
        # Sanity check size > 100 bytes
        assert os.path.getsize(actual) > 100
