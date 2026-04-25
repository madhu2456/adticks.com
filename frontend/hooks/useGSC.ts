"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useGSCMetrics(projectId: string, days = 28) {
  return useQuery({
    queryKey: ["gsc-metrics", projectId, days],
    queryFn: () => api.gsc.getMetrics(projectId, days),
    staleTime: 5 * 60 * 1000,
    enabled: !!projectId,
  });
}

export function useGSCQueries(projectId: string) {
  return useQuery({
    queryKey: ["gsc-queries", projectId],
    queryFn: () => api.gsc.getQueries(projectId),
    staleTime: 5 * 60 * 1000,
    enabled: !!projectId,
  });
}

export function useGSCProperties() {
  return useQuery({
    queryKey: ["gsc-properties"],
    queryFn: () => api.gsc.listProperties(),
    staleTime: 10 * 60 * 1000,
  });
}
