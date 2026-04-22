"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { mockGSCMetrics, mockGSCQueries } from "@/lib/mockData";

export function useGSCMetrics(projectId: string, days = 28) {
  return useQuery({
    queryKey: ["gsc-metrics", projectId, days],
    queryFn: () => api.gsc.getMetrics(projectId, days).catch(() => mockGSCMetrics),
    staleTime: 5 * 60 * 1000,
  });
}

export function useGSCQueries(projectId: string) {
  return useQuery({
    queryKey: ["gsc-queries", projectId],
    queryFn: () => api.gsc.getQueries(projectId).catch(() => mockGSCQueries),
    staleTime: 5 * 60 * 1000,
  });
}
