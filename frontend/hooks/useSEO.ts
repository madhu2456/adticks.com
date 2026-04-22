"use client";
import { useQuery, useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import {
  mockKeywords, mockContentGaps, mockOnPageAudit, mockTechnicalChecks,
} from "@/lib/mockData";

export function useKeywords(projectId: string, search?: string) {
  return useQuery({
    queryKey: ["keywords", projectId, search],
    queryFn: () =>
      api.seo.getKeywords(projectId, 1, search).catch(() => ({
        items: mockKeywords.filter((k) =>
          search ? k.keyword.toLowerCase().includes(search.toLowerCase()) : true
        ),
        total: mockKeywords.length,
        page: 1,
        per_page: 20,
        pages: 1,
      })),
    staleTime: 2 * 60 * 1000,
  });
}

export function useContentGaps(projectId: string) {
  return useQuery({
    queryKey: ["content-gaps", projectId],
    queryFn: () => api.seo.getGaps(projectId).catch(() => mockContentGaps),
    staleTime: 5 * 60 * 1000,
  });
}

export function useOnPageAudit(projectId: string, url?: string) {
  return useQuery({
    queryKey: ["audit", projectId, url],
    queryFn: () => (url ? api.seo.runAudit(projectId, url) : Promise.resolve(mockOnPageAudit)),
    enabled: !!url,
    staleTime: 60 * 1000,
  });
}

export function useTechnicalChecks(projectId: string) {
  return useQuery({
    queryKey: ["technical", projectId],
    queryFn: () => api.seo.getTechnicalChecks(projectId).catch(() => mockTechnicalChecks),
    staleTime: 10 * 60 * 1000,
  });
}
