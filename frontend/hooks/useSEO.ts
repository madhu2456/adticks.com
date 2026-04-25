"use client";
import { useQuery, useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useKeywords(projectId: string, search?: string) {
  return useQuery({
    queryKey: ["keywords", projectId, search],
    queryFn: () => api.seo.getKeywords(projectId, 1, search),
    staleTime: 2 * 60 * 1000,
  });
}

export function useContentGaps(projectId: string) {
  return useQuery({
    queryKey: ["content-gaps", projectId],
    queryFn: () => api.seo.getGaps(projectId),
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Hook to fetch the most recent on-page audit results from cache.
 */
export function useOnPageAudit(projectId: string) {
  return useQuery({
    queryKey: ["onpage-audit", projectId],
    queryFn: () => api.seo.getOnPageAudit(projectId),
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Hook to trigger a new audit.
 */
export function useTriggerOnPageAudit() {
  return useMutation({
    mutationFn: ({ projectId, url }: { projectId: string, url: string }) => 
      api.seo.runAudit(projectId, url),
  });
}

export function useTechnicalChecks(projectId: string) {
  return useQuery({
    queryKey: ["technical", projectId],
    queryFn: () => api.seo.getTechnicalChecks(projectId),
    staleTime: 10 * 60 * 1000,
  });
}
