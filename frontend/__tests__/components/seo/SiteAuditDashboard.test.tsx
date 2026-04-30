import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { SiteAuditDashboard } from "@/components/seo/SiteAuditDashboard";

jest.mock("@/hooks/useSEO", () => ({
  useAuditSummary: jest.fn(),
  useAuditIssues: jest.fn(),
  useCrawledPages: jest.fn(),
  useRunSiteAudit: jest.fn(),
}));

import {
  useAuditSummary,
  useAuditIssues,
  useCrawledPages,
  useRunSiteAudit,
} from "@/hooks/useSEO";

const mSummary = useAuditSummary as jest.Mock;
const mIssues = useAuditIssues as jest.Mock;
const mPages = useCrawledPages as jest.Mock;
const mRun = useRunSiteAudit as jest.Mock;

beforeEach(() => {
  mSummary.mockReturnValue({ isLoading: false, data: null, refetch: jest.fn() });
  mIssues.mockReturnValue({ isLoading: false, data: [], refetch: jest.fn() });
  mPages.mockReturnValue({ data: [] });
  mRun.mockReturnValue({ isPending: false, mutateAsync: jest.fn(), isError: false });
});

describe("SiteAuditDashboard", () => {
  it("renders the run-audit form", () => {
    render(<SiteAuditDashboard projectId="p1"/>);
    expect(screen.getByPlaceholderText(/https:\/\/example.com/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /run audit/i })).toBeInTheDocument();
  });

  it("disables Run button while pending", () => {
    mRun.mockReturnValue({ isPending: true, mutateAsync: jest.fn(), isError: false });
    render(<SiteAuditDashboard projectId="p1" defaultUrl="https://x.com"/>);
    const btn = screen.getByRole("button", { name: /crawling/i });
    expect(btn).toBeDisabled();
  });

  it("triggers mutation when Run clicked", async () => {
    const mutateAsync = jest.fn().mockResolvedValue({});
    mRun.mockReturnValue({ isPending: false, mutateAsync, isError: false });
    render(<SiteAuditDashboard projectId="p1" defaultUrl="https://x.com"/>);
    fireEvent.click(screen.getByRole("button", { name: /run audit/i }));
    await waitFor(() => expect(mutateAsync).toHaveBeenCalledWith({
      projectId: "p1", url: "https://x.com", max_pages: 50, max_depth: 3,
    }));
  });

  it("renders summary cards when data is present", () => {
    mSummary.mockReturnValue({
      isLoading: false,
      data: {
        score: 82, total_pages: 35, errors: 2, warnings: 5, notices: 3,
        total_issues: 10, avg_response_time_ms: 120,
        issues_by_category: { on_page: 5, security: 1 },
      },
      refetch: jest.fn(),
    });
    render(<SiteAuditDashboard projectId="p1"/>);
    expect(screen.getByText("Health Score")).toBeInTheDocument();
    expect(screen.getByText("82")).toBeInTheDocument();
    expect(screen.getByText("35")).toBeInTheDocument();
  });

  it("renders an empty state when there are no issues", () => {
    render(<SiteAuditDashboard projectId="p1"/>);
    expect(screen.getByText(/no issues found/i)).toBeInTheDocument();
  });

  it("renders issue rows", () => {
    mIssues.mockReturnValue({
      isLoading: false,
      data: [{
        id: "i1", url: "https://x.com/a", category: "on_page",
        severity: "error", code: "title-missing", message: "No title",
        recommendation: "Add a title", details: {},
      }],
      refetch: jest.fn(),
    });
    render(<SiteAuditDashboard projectId="p1"/>);
    expect(screen.getByText("No title")).toBeInTheDocument();
    expect(screen.getAllByText("on_page")[0]).toBeInTheDocument();
    expect(screen.getByText("title-missing")).toBeInTheDocument();
    expect(screen.getByText(/Add a title/)).toBeInTheDocument();
  });
});
