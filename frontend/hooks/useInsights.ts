"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { mockInsights, mockRecommendations } from "@/lib/mockData";
import { InsightCategory, InsightPriority } from "@/lib/types";

export function useInsights(projectId: string, category?: InsightCategory, priority?: InsightPriority) {
  return useQuery({
    queryKey: ["insights", projectId, category, priority],
    queryFn: () =>
      api.insights.getInsights(projectId, category, priority).catch(() =>
        mockInsights.filter((i) => {
          if (category && i.category !== category) return false;
          if (priority && i.priority !== priority) return false;
          return true;
        })
      ),
    staleTime: 2 * 60 * 1000,
  });
}

export function useRecommendations(projectId: string) {
  return useQuery({
    queryKey: ["recommendations", projectId],
    queryFn: () => api.insights.getRecommendations(projectId).catch(() => mockRecommendations),
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
