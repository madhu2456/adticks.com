import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import { useInsights, useRecommendations, useRefreshInsights } from "@/hooks/useInsights";
import { Insight, Recommendation } from "@/lib/types";

jest.mock("@/lib/api", () => ({
  api: {
    insights: {
      getInsights: jest.fn(),
      getRecommendations: jest.fn(),
      refresh: jest.fn(),
    },
  },
}));

import { api } from "@/lib/api";
const mockApi = api as jest.Mocked<typeof api>;

const mockInsightsData: Insight[] = [
  {
    id: "ins1",
    title: "Fix title tags",
    description: "Title tags are missing.",
    category: "seo",
    priority: "P1",
    created_at: new Date().toISOString(),
    is_read: false,
  },
  {
    id: "ins2",
    title: "AI brand mentions low",
    description: "Brand not mentioned enough in AI results.",
    category: "ai",
    priority: "P2",
    created_at: new Date().toISOString(),
    is_read: true,
  },
];

const mockRecommendationsData: Recommendation[] = [
  {
    id: "rec1",
    title: "Fix title tags action",
    description: "Add unique title tags to all pages.",
    priority: "P1",
    category: "seo",
    effort: "low",
    impact: "high",
  },
];

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children);
}

describe("useInsights", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("returns data after successful fetch", async () => {
    (mockApi.insights.getInsights as jest.Mock).mockResolvedValue(mockInsightsData);
    const { result } = renderHook(() => useInsights("proj1"), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockInsightsData);
  });

  it("starts in loading state", () => {
    let resolve: (v: Insight[]) => void;
    const promise = new Promise<Insight[]>((res) => { resolve = res; });
    (mockApi.insights.getInsights as jest.Mock).mockReturnValue(promise);
    const { result } = renderHook(() => useInsights("proj1"), { wrapper: createWrapper() });
    expect(result.current.isLoading).toBe(true);
    resolve!(mockInsightsData);
  });

  it("handles API errors by returning empty data", async () => {
    (mockApi.insights.getInsights as jest.Mock).mockRejectedValue(new Error("Server error"));
    const { result } = renderHook(() => useInsights("proj1"), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual({ data: [] });
  });

  it("filters by category when category param is provided", async () => {
    const seoInsights = mockInsightsData.filter((i) => i.category === "seo");
    (mockApi.insights.getInsights as jest.Mock).mockResolvedValue(seoInsights);
    const { result } = renderHook(
      () => useInsights("proj1", "seo"),
      { wrapper: createWrapper() }
    );
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockApi.insights.getInsights).toHaveBeenCalledWith("proj1", "seo", undefined);
  });

  it("filters by priority when priority param is provided", async () => {
    const p1Insights = mockInsightsData.filter((i) => i.priority === "P1");
    (mockApi.insights.getInsights as jest.Mock).mockResolvedValue(p1Insights);
    const { result } = renderHook(
      () => useInsights("proj1", undefined, "P1"),
      { wrapper: createWrapper() }
    );
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockApi.insights.getInsights).toHaveBeenCalledWith("proj1", undefined, "P1");
  });

  it("includes projectId in the query key", async () => {
    (mockApi.insights.getInsights as jest.Mock).mockResolvedValue(mockInsightsData);
    const { result } = renderHook(() => useInsights("proj2"), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockApi.insights.getInsights).toHaveBeenCalledWith("proj2", undefined, undefined);
  });
});

describe("useRecommendations", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("returns recommendations after successful fetch", async () => {
    (mockApi.insights.getRecommendations as jest.Mock).mockResolvedValue(mockRecommendationsData);
    const { result } = renderHook(() => useRecommendations("proj1"), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockRecommendationsData);
  });

  it("starts in loading state", () => {
    let resolve: (v: Recommendation[]) => void;
    const promise = new Promise<Recommendation[]>((res) => { resolve = res; });
    (mockApi.insights.getRecommendations as jest.Mock).mockReturnValue(promise);
    const { result } = renderHook(() => useRecommendations("proj1"), { wrapper: createWrapper() });
    expect(result.current.isLoading).toBe(true);
    resolve!(mockRecommendationsData);
  });

  it("handles API errors gracefully", async () => {
    (mockApi.insights.getRecommendations as jest.Mock).mockRejectedValue(new Error("fail"));
    const { result } = renderHook(() => useRecommendations("proj1"), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toBeDefined();
  });

  it("each recommendation has required fields", async () => {
    (mockApi.insights.getRecommendations as jest.Mock).mockResolvedValue(mockRecommendationsData);
    const { result } = renderHook(() => useRecommendations("proj1"), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    const rec = result.current.data![0];
    expect(rec).toHaveProperty("id");
    expect(rec).toHaveProperty("title");
    expect(rec).toHaveProperty("description");
    expect(rec).toHaveProperty("priority");
    expect(rec).toHaveProperty("category");
  });
});

describe("useRefreshInsights", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("exposes mutate function", () => {
    const { result } = renderHook(() => useRefreshInsights("proj1"), { wrapper: createWrapper() });
    expect(typeof result.current.mutate).toBe("function");
  });

  it("calls api.insights.refresh when mutate is triggered", async () => {
    (mockApi.insights.refresh as jest.Mock).mockResolvedValue({ job_id: "job123" });
    // Also mock getInsights so invalidation doesn't fail
    (mockApi.insights.getInsights as jest.Mock).mockResolvedValue(mockInsightsData);
    const { result } = renderHook(() => useRefreshInsights("proj1"), { wrapper: createWrapper() });
    result.current.mutate();
    await waitFor(() => expect(mockApi.insights.refresh).toHaveBeenCalledWith("proj1"));
  });
});
