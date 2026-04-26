"use client";
import { useQuery, useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useKeywords(projectId: string, search?: string) {
  return useQuery({
    queryKey: ["keywords", projectId, search],
    queryFn: () => api.seo.getKeywords(projectId, 1, search),
    staleTime: 2 * 60 * 1000,
    enabled: !!projectId,
  });
}

export function useContentGaps(projectId: string) {
  return useQuery({
    queryKey: ["content-gaps", projectId],
    queryFn: () => api.seo.getGaps(projectId),
    staleTime: 5 * 60 * 1000,
    enabled: !!projectId,
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
    enabled: !!projectId,
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
    enabled: !!projectId,
  });
}

export function useRankHistory(projectId: string, keywordId?: string, days = 30) {
  return useQuery({
    queryKey: ["rankHistory", projectId, keywordId, days],
    queryFn: () => api.seoSuite.getRankHistory(projectId, keywordId, days, 0, 100),
    staleTime: 5 * 60 * 1000,
    enabled: !!projectId,
  });
}

export function useClusters(projectId: string) {
  return useQuery({
    queryKey: ["clusters", projectId],
    queryFn: () => api.clusters.list(projectId),
    enabled: !!projectId,
  });
}

export function useCreateCluster() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId, data }: { projectId: string; data: any }) =>
      api.clusters.create(projectId, data),
    onSuccess: (_, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: ["clusters", projectId] });
      queryClient.invalidateQueries({ queryKey: ["keywords", projectId] });
    },
  });
}

export function useBacklinks(projectId: string, skip = 0, limit = 50, minAuthority?: number) {
  return useQuery({
    queryKey: ["backlinks", projectId, skip, limit, minAuthority],
    queryFn: () => api.seoSuite.getBacklinks(projectId, skip, limit, minAuthority),
    enabled: !!projectId,
  });
}

export function useBacklinkStats(projectId: string) {
  return useQuery({
    queryKey: ["backlinkStats", projectId],
    queryFn: () => api.seoSuite.getBacklinkStats(projectId),
    enabled: !!projectId,
  });
}

export function useBacklinkIntersect(projectId: string) {
  return useQuery({
    queryKey: ["backlinkIntersect", projectId],
    queryFn: () => api.seoSuite.getBacklinkIntersect(projectId),
    enabled: !!projectId,
  });
}

export function useAuditHistory(projectId: string) {
  return useQuery({
    queryKey: ["auditHistory", projectId],
    queryFn: () => api.seoSuite.getAuditHistory(projectId),
    enabled: !!projectId,
  });
}

export function useSOV(projectId: string) {
  return useQuery({
    queryKey: ["sov", projectId],
    queryFn: () => api.seo.getSOV(projectId),
    enabled: !!projectId,
  });
}
