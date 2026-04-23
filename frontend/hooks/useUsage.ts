"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface UsageStats {
  ai_scans_used: number;
  ai_scans_limit: number;
  keywords_used: number;
  keywords_limit: number;
  competitors_used: number;
  competitors_limit: number;
  days_remaining: number;
  plan: string;
  api_requests_today: number;
  api_requests_month: number;
  api_rate_limit: string;
}

export function useUsage() {
  return useQuery({
    queryKey: ["usage"],
    queryFn: () => api.auth.getUsage().catch(() => ({
      ai_scans_used: 0,
      ai_scans_limit: 50,
      keywords_used: 0,
      keywords_limit: 500,
      competitors_used: 0,
      competitors_limit: 3,
      days_remaining: 14,
      plan: "free",
      api_requests_today: 0,
      api_requests_month: 0,
      api_rate_limit: "100/hr",
    })),
    staleTime: 5 * 60 * 1000,
  });
}
