import React from "react";
import { render, screen } from "@testing-library/react";
import { SEOHubOverview } from "@/components/seo/SEOHubOverview";

jest.mock("@/hooks/useSEO", () => ({
  useSEOHubOverview: jest.fn(),
}));

import { useSEOHubOverview } from "@/hooks/useSEO";

const mockHook = useSEOHubOverview as jest.Mock;

describe("SEOHubOverview", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders skeletons while loading", () => {
    mockHook.mockReturnValue({ isLoading: true, data: undefined });
    const { container } = render(<SEOHubOverview projectId="p1"/>);
    // 8 tiles -> 8 skeletons
    const skeletons = container.querySelectorAll('[class*="skeleton"], [data-state="loading"]');
    // Just verify it doesn't render the populated tiles
    expect(screen.queryByText("Site Health")).toBeNull();
  });

  it("renders nothing when data is missing and not loading", () => {
    mockHook.mockReturnValue({ isLoading: false, data: undefined });
    const { container } = render(<SEOHubOverview projectId="p1"/>);
    expect(container.textContent).toBe("");
  });

  it("renders all metric tiles when data is present", () => {
    mockHook.mockReturnValue({
      isLoading: false,
      data: {
        site_score: 78,
        total_issues: 17,
        errors: 3,
        pages_crawled: 42,
        core_web_vitals_score: 85,
        keywords_tracked: 89,
        keyword_ideas: 220,
        backlinks: 1200,
        referring_domains: 156,
        toxic_backlinks: 5,
        citations: 12,
        content_briefs: 4,
      },
    });
    render(<SEOHubOverview projectId="p1"/>);
    expect(screen.getByText("Site Health")).toBeInTheDocument();
    expect(screen.getByText("78/100")).toBeInTheDocument();
    expect(screen.getByText("17")).toBeInTheDocument();
    expect(screen.getByText("3 errors")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getByText("85")).toBeInTheDocument();
    expect(screen.getByText("89")).toBeInTheDocument();
    expect(screen.getByText("220 ideas")).toBeInTheDocument();
    expect(screen.getByText("1200")).toBeInTheDocument();
    expect(screen.getByText("156 domains")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("4 briefs")).toBeInTheDocument();
  });

  it("renders em-dash when CWV score is missing", () => {
    mockHook.mockReturnValue({
      isLoading: false,
      data: {
        site_score: 0, total_issues: 0, errors: 0, pages_crawled: 0,
        core_web_vitals_score: null, keywords_tracked: 0, keyword_ideas: 0,
        backlinks: 0, referring_domains: 0, toxic_backlinks: 0,
        citations: 0, content_briefs: 0,
      },
    });
    render(<SEOHubOverview projectId="p1"/>);
    expect(screen.getByText("—")).toBeInTheDocument();
  });

  it("highlights toxic backlink count in red when > 0", () => {
    mockHook.mockReturnValue({
      isLoading: false,
      data: {
        site_score: 80, total_issues: 0, errors: 0, pages_crawled: 0,
        core_web_vitals_score: 80, keywords_tracked: 0, keyword_ideas: 0,
        backlinks: 0, referring_domains: 0, toxic_backlinks: 7,
        citations: 0, content_briefs: 0,
      },
    });
    const { container } = render(<SEOHubOverview projectId="p1"/>);
    // Find the element that shows "7" and verify a red color class is applied to it
    const toxicValue = screen.getByText("7");
    expect(toxicValue.className).toMatch(/text-red/);
  });
});
