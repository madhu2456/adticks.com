"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useAIScore(projectId: string) {
  return useQuery({
    queryKey: ["ai-score", projectId],
    queryFn: () => api.ai.getScore(projectId),
    staleTime: 5 * 60 * 1000,
  });
}

export function useSOV(projectId: string) {
  return useQuery({
    queryKey: ["sov", projectId],
    queryFn: () => api.ai.getSOV(projectId),
    staleTime: 5 * 60 * 1000,
  });
}

export function useCategoryBreakdown(projectId: string) {
  return useQuery({
    queryKey: ["ai-categories", projectId],
    queryFn: () => api.ai.getCategoryBreakdown(projectId),
    staleTime: 5 * 60 * 1000,
  });
}

export function useAIResults(projectId: string) {
  return useQuery({
    queryKey: ["ai-results", projectId],
    queryFn: () => api.ai.getMentions(projectId),
    staleTime: 2 * 60 * 1000,
  });
}

export function useRunAIScan(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.ai.runScan(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ai-score", projectId] });
      queryClient.invalidateQueries({ queryKey: ["ai-results", projectId] });
    },
  });
}
