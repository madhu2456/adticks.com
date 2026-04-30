"""Unit tests for app.services.seo.internal_links."""
from __future__ import annotations

import pytest

from app.services.seo.internal_links import (
    parse_links_for_page,
    analyze_graph,
    LinkRow,
    _same_origin,
)


class TestParseLinksForPage:
    def test_parses_internal_links(self):
        html = """
        <html><body>
          <a href="/about">About</a>
          <a href="https://example.com/contact">Contact</a>
          <a href="https://other-site.com/x">External</a>
          <a href="mailto:hi@example.com">Email</a>
          <a href="#anchor">Anchor</a>
        </body></html>
        """
        rows = parse_links_for_page(html, "https://example.com/")
        # External, mailto, and anchor-only filtered out
        assert len(rows) == 2
        targets = {r.target_url for r in rows}
        assert "https://example.com/about" in targets
        assert "https://example.com/contact" in targets

    def test_detects_nofollow(self):
        html = '<html><body><a href="/x" rel="nofollow">x</a></body></html>'
        rows = parse_links_for_page(html, "https://example.com/")
        assert rows[0].is_nofollow is True

    def test_link_position_nav(self):
        html = """
        <html><body>
          <nav><a href="/a">A</a></nav>
          <main><a href="/b">B</a></main>
          <footer><a href="/c">C</a></footer>
        </body></html>
        """
        rows = parse_links_for_page(html, "https://example.com/")
        positions = {r.target_url: r.link_position for r in rows}
        assert positions["https://example.com/a"] == "nav"
        assert positions["https://example.com/b"] == "body"
        assert positions["https://example.com/c"] == "footer"

    def test_anchor_text_captured(self):
        html = '<html><body><a href="/x">Click here</a></body></html>'
        rows = parse_links_for_page(html, "https://example.com/")
        assert rows[0].anchor_text == "Click here"


class TestSameOrigin:
    def test_strips_www(self):
        assert _same_origin("https://example.com/x", "https://www.example.com/y") is True

    def test_different_hosts(self):
        assert _same_origin("https://example.com", "https://other.com") is False


class TestAnalyzeGraph:
    def test_builds_graph_and_finds_orphans(self):
        edges = [
            LinkRow(source_url="A", target_url="B"),
            LinkRow(source_url="A", target_url="C"),
            LinkRow(source_url="B", target_url="C"),
        ]
        # D is in `all_pages` but never linked to → orphan
        graph = analyze_graph(edges, all_pages={"A", "B", "C", "D"})
        assert graph.in_degree.get("C", 0) == 2
        assert graph.in_degree.get("B", 0) == 1
        assert graph.out_degree.get("A", 0) == 2
        assert "D" in graph.orphans
        # C has no outbound links → dead-end
        assert "C" in graph.dead_ends
        # D has neither in nor out → both
        assert "D" in graph.dead_ends

    def test_empty_input_returns_empty(self):
        graph = analyze_graph([])
        assert graph.edges == []
        assert graph.nodes == set()
        assert graph.orphans == []

    def test_page_authority_normalized(self):
        edges = [
            LinkRow(source_url="A", target_url="B"),
            LinkRow(source_url="A", target_url="B"),
            LinkRow(source_url="C", target_url="B"),
            LinkRow(source_url="A", target_url="D"),
        ]
        graph = analyze_graph(edges)
        assert graph.page_authority["B"] >= graph.page_authority["D"]
        # PA should be in [0, 100]
        for v in graph.page_authority.values():
            assert 0 <= v <= 100
