"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { InsightCategory, InsightPriority } from "@/lib/types";

export function useInsights(projectId: string, category?: InsightCategory, priority?: InsightPriority) {
  return useQuery({
    queryKey: ["insights", projectId, category, priority],
    queryFn: async () => {
      if (!projectId) return { data: [] };
      try {
        return await api.insights.getInsights(projectId, category, priority);
      } catch (err) {
        console.error("Failed to fetch insights:", err);
        return { data: [] };
      }
    },
    staleTime: 2 * 60 * 1000,
  });
}

export function useRecommendations(projectId: string) {
  return useQuery({
    queryKey: ["recommendations", projectId],
    queryFn: () => api.insights.getRecommendations(projectId),
    staleTime: 5 * 60 * 1000,
  });
}

export function useRefreshInsights(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.insights.refresh(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["insights", projectId] });
    },
  });
}
