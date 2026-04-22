"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { mockCampaigns, mockAdsPerformance } from "@/lib/mockData";

export function useCampaigns(projectId: string) {
  return useQuery({
    queryKey: ["campaigns", projectId],
    queryFn: () => api.ads.getCampaigns(projectId).catch(() => mockCampaigns),
    staleTime: 5 * 60 * 1000,
  });
}

export function useAdsPerformance(projectId: string, days = 30) {
  return useQuery({
    queryKey: ["ads-performance", projectId, days],
    queryFn: () => api.ads.getPerformance(projectId, days).catch(() => mockAdsPerformance),
    staleTime: 5 * 60 * 1000,
  });
}
