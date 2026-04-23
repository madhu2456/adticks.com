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

export function useOnPageAudit(projectId: string, url?: string) {
  return useQuery({
    queryKey: ["audit", projectId, url],
    queryFn: () => (url ? api.seo.runAudit(projectId, url) : Promise.reject(new Error("URL required"))),
    enabled: !!url,
    staleTime: 60 * 1000,
  });
}

export function useTechnicalChecks(projectId: string) {
  return useQuery({
    queryKey: ["technical", projectId],
    queryFn: () => api.seo.getTechnicalChecks(projectId),
    staleTime: 10 * 60 * 1000,
  });
}
