import React from "react";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

jest.mock("@/lib/api", () => ({
  api: {
    seoAdvanced: {
      hubOverview: jest.fn(),
      getAuditSummary: jest.fn(),
      getAuditIssues: jest.fn(),
      getCrawledPages: jest.fn(),
      getSchemas: jest.fn(),
      runAudit: jest.fn(),
      getCWV: jest.fn(),
      runCWV: jest.fn(),
      getKeywordIdeas: jest.fn(),
      keywordMagic: jest.fn(),
      analyzeSerp: jest.fn(),
      getAnchors: jest.fn(),
      refreshAnchors: jest.fn(),
      getToxic: jest.fn(),
      scanToxic: jest.fn(),
      disavowToxic: jest.fn(),
      intersect: jest.fn(),
      listBriefs: jest.fn(),
      createBrief: jest.fn(),
      optimize: jest.fn(),
      listClusters: jest.fn(),
      buildCluster: jest.fn(),
      getCitations: jest.fn(),
      getConsistency: jest.fn(),
      getGrid: jest.fn(),
      runGrid: jest.fn(),
      getLogs: jest.fn(),
      uploadLog: jest.fn(),
      listReports: jest.fn(),
      generateReport: jest.fn(),
    },
  },
}));

import { api } from "@/lib/api";
import * as hooks from "@/hooks/useSEO";

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
}

describe("useSEO advanced hooks", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("useSEOHubOverview calls api.seoAdvanced.hubOverview", async () => {
    (api.seoAdvanced.hubOverview as jest.Mock).mockResolvedValue({ site_score: 80 });
    const { result } = renderHook(() => hooks.useSEOHubOverview("p1"), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.data).toEqual({ site_score: 80 }));
    expect(api.seoAdvanced.hubOverview).toHaveBeenCalledWith("p1");
  });

  it("useAuditSummary fetches summary", async () => {
    (api.seoAdvanced.getAuditSummary as jest.Mock).mockResolvedValue({ score: 90 });
    const { result } = renderHook(() => hooks.useAuditSummary("p1"), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.data).toEqual({ score: 90 }));
  });

  it("useAuditIssues passes severity & category filters", async () => {
    (api.seoAdvanced.getAuditIssues as jest.Mock).mockResolvedValue([]);
    const { result } = renderHook(() => hooks.useAuditIssues("p1", "error", "on_page"), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(api.seoAdvanced.getAuditIssues).toHaveBeenCalledWith(
      "p1", { severity: "error", category: "on_page", limit: 200 },
    );
  });

  it("useRunSiteAudit invokes mutation with all args", async () => {
    (api.seoAdvanced.runAudit as jest.Mock).mockResolvedValue({ status: "completed" });
    const { result } = renderHook(() => hooks.useRunSiteAudit(), { wrapper: makeWrapper() });
    await act(async () => {
      await result.current.mutateAsync({
        projectId: "p1", url: "https://x.com", max_pages: 10, max_depth: 2,
      });
    });
    expect(api.seoAdvanced.runAudit).toHaveBeenCalledWith("p1", "https://x.com", 10, 2);
  });

  it("useKeywordMagic mutation passes payload", async () => {
    (api.seoAdvanced.keywordMagic as jest.Mock).mockResolvedValue([]);
    const { result } = renderHook(() => hooks.useKeywordMagic(), { wrapper: makeWrapper() });
    await act(async () => {
      await result.current.mutateAsync({
        projectId: "p1",
        payload: { seed: "seo", limit: 80 },
      });
    });
    expect(api.seoAdvanced.keywordMagic).toHaveBeenCalledWith("p1", { seed: "seo", limit: 80 });
  });

  it("useAnalyzeSerp calls analyzeSerp with all params", async () => {
    (api.seoAdvanced.analyzeSerp as jest.Mock).mockResolvedValue({ results: [] });
    const { result } = renderHook(() => hooks.useAnalyzeSerp(), { wrapper: makeWrapper() });
    await act(async () => {
      await result.current.mutateAsync({
        projectId: "p1", keyword: "x", location: "uk", device: "mobile",
      });
    });
    expect(api.seoAdvanced.analyzeSerp).toHaveBeenCalledWith("p1", "x", "uk", "mobile");
  });

  it("useScanToxic + useDisavowToxic call right APIs", async () => {
    (api.seoAdvanced.scanToxic as jest.Mock).mockResolvedValue({ toxic_count: 1 });
    (api.seoAdvanced.disavowToxic as jest.Mock).mockResolvedValue({ status: "disavowed" });

    const { result: scan } = renderHook(() => hooks.useScanToxic(), { wrapper: makeWrapper() });
    await act(async () => { await scan.current.mutateAsync({ projectId: "p1", minScore: 50 }); });
    expect(api.seoAdvanced.scanToxic).toHaveBeenCalledWith("p1", 50);

    const { result: disavow } = renderHook(() => hooks.useDisavowToxic(), { wrapper: makeWrapper() });
    await act(async () => { await disavow.current.mutateAsync({ projectId: "p1", toxicId: "t1" }); });
    expect(api.seoAdvanced.disavowToxic).toHaveBeenCalledWith("p1", "t1");
  });

  it("useGenerateReport passes branding payload", async () => {
    (api.seoAdvanced.generateReport as jest.Mock).mockResolvedValue({ id: "r1" });
    const { result } = renderHook(() => hooks.useGenerateReport(), { wrapper: makeWrapper() });
    await act(async () => {
      await result.current.mutateAsync({
        projectId: "p1",
        payload: { report_type: "full_seo", title: "X", branding: { brand_name: "B" } },
      });
    });
    expect(api.seoAdvanced.generateReport).toHaveBeenCalledWith("p1", expect.objectContaining({
      report_type: "full_seo", title: "X", branding: { brand_name: "B" },
    }));
  });

  it("useUploadLogFile mutation passes file", async () => {
    (api.seoAdvanced.uploadLog as jest.Mock).mockResolvedValue({ summary: {} });
    const { result } = renderHook(() => hooks.useUploadLogFile(), { wrapper: makeWrapper() });
    const file = new File(["x"], "a.log", { type: "text/plain" });
    await act(async () => { await result.current.mutateAsync({ projectId: "p1", file }); });
    expect(api.seoAdvanced.uploadLog).toHaveBeenCalledWith("p1", file);
  });
});
