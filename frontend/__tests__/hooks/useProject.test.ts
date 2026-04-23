import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import { useProjects, useProject, useActiveProject } from "@/hooks/useProject";
import { Project } from "@/lib/types";

jest.mock("@/lib/api", () => ({
  api: {
    projects: {
      list: jest.fn(),
      create: jest.fn(),
      get: jest.fn(),
    },
  },
}));

import { api } from "@/lib/api";
const mockApi = api as jest.Mocked<typeof api>;

const MOCK_PROJECTS: Project[] = [
  {
    id: "proj1",
    name: "AdTicks.io",
    domain: "adticks.io",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    gsc_connected: true,
    ads_connected: true,
  },
  {
    id: "proj2",
    name: "Marketing Blog",
    domain: "blog.adticks.io",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    gsc_connected: false,
    ads_connected: false,
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

describe("useProjects", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("is initially empty before data arrives", () => {
    (mockApi.projects.list as jest.Mock).mockResolvedValue(MOCK_PROJECTS);
    const { result } = renderHook(() => useProjects(), { wrapper: createWrapper() });
    // Should be undefined until fetch starts/completes
    expect(result.current.data).toBeUndefined();
  });

  it("returns data after successful fetch", async () => {
    (mockApi.projects.list as jest.Mock).mockResolvedValue(MOCK_PROJECTS);
    const { result } = renderHook(() => useProjects(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(expect.arrayContaining([
      expect.objectContaining({ id: "proj1", name: "AdTicks.io" }),
    ]));
  });

  it("falls back to empty array when API fails", async () => {
    (mockApi.projects.list as jest.Mock).mockRejectedValue(new Error("Network error"));
    const { result } = renderHook(() => useProjects(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    // The hook catches the error and falls back to []
    expect(result.current.data).toEqual([]);
  });

  it("data includes expected project fields", async () => {
    (mockApi.projects.list as jest.Mock).mockResolvedValue(MOCK_PROJECTS);
    const { result } = renderHook(() => useProjects(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    const project = result.current.data![0];
    expect(project).toHaveProperty("id");
    expect(project).toHaveProperty("name");
    expect(project).toHaveProperty("domain");
    expect(project).toHaveProperty("gsc_connected");
    expect(project).toHaveProperty("ads_connected");
  });
});

describe("useProject", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("returns a single project by id after successful fetch", async () => {
    (mockApi.projects.get as jest.Mock).mockResolvedValue(MOCK_PROJECTS[0]);
    const { result } = renderHook(() => useProject("proj1"), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(expect.objectContaining({ id: "proj1" }));
  });

  it("starts in loading state before data arrives", async () => {
    let resolve: (v: any) => void;
    const promise = new Promise((res) => { resolve = res; });
    (mockApi.projects.get as jest.Mock).mockReturnValue(promise);
    const { result } = renderHook(() => useProject("proj1"), { wrapper: createWrapper() });
    expect(result.current.isLoading).toBe(true);
    resolve!(MOCK_PROJECTS[0]);
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });

  it("falls back to null when API fails for useProject", async () => {
    (mockApi.projects.get as jest.Mock).mockRejectedValue(new Error("Not found"));
    const { result } = renderHook(() => useProject("proj1"), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toBeNull();
  });
});

describe("useActiveProject", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("returns activeProject, activeId, setActiveId, and projects array", async () => {
    (mockApi.projects.list as jest.Mock).mockResolvedValue(MOCK_PROJECTS);
    const { result } = renderHook(() => useActiveProject(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.projects.length).toBeGreaterThan(0));
    expect(result.current).toHaveProperty("activeProject");
    expect(result.current).toHaveProperty("activeId");
    expect(result.current).toHaveProperty("setActiveId");
    expect(result.current).toHaveProperty("projects");
  });

  it("defaults activeId and activeProject to first project", async () => {
    (mockApi.projects.list as jest.Mock).mockResolvedValue(MOCK_PROJECTS);
    const { result } = renderHook(() => useActiveProject(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.projects.length).toBeGreaterThan(0));
    expect(result.current.activeId).toBe("proj1");
    expect(result.current.activeProject?.id).toBe("proj1");
  });
});
