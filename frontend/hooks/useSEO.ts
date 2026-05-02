"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
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

// ============================================================================
// Advanced SEO Suite hooks (Ahrefs / SEMrush / Moz superset)
// ============================================================================

export function useSEOHubOverview(projectId: string) {
  return useQuery({
    queryKey: ["seoHubOverview", projectId],
    queryFn: () => api.seoAdvanced.hubOverview(projectId),
    enabled: !!projectId,
    staleTime: 60_000,
  });
}

export function useAuditSummary(projectId: string) {
  return useQuery({
    queryKey: ["auditSummary", projectId],
    queryFn: () => api.seoAdvanced.getAuditSummary(projectId),
    enabled: !!projectId,
  });
}

export function useAuditIssues(projectId: string, severity?: string, category?: string) {
  return useQuery({
    queryKey: ["auditIssues", projectId, severity, category],
    queryFn: () => api.seoAdvanced.getAuditIssues(projectId, { severity, category, limit: 200 }),
    enabled: !!projectId,
  });
}

export function useCrawledPages(projectId: string) {
  return useQuery({
    queryKey: ["crawledPages", projectId],
    queryFn: () => api.seoAdvanced.getCrawledPages(projectId),
    enabled: !!projectId,
  });
}

export function useSchemas(projectId: string) {
  return useQuery({
    queryKey: ["schemas", projectId],
    queryFn: () => api.seoAdvanced.getSchemas(projectId),
    enabled: !!projectId,
  });
}

export function useRunSiteAudit() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId, url, max_pages, max_depth }: { projectId: string; url: string; max_pages?: number; max_depth?: number }) =>
      api.seoAdvanced.runAudit(projectId, url, max_pages, max_depth),
    onSuccess: (_, { projectId }) => {
      qc.invalidateQueries({ queryKey: ["auditSummary", projectId] });
      qc.invalidateQueries({ queryKey: ["auditIssues", projectId] });
      qc.invalidateQueries({ queryKey: ["crawledPages", projectId] });
      qc.invalidateQueries({ queryKey: ["schemas", projectId] });
      qc.invalidateQueries({ queryKey: ["seoHubOverview", projectId] });
    },
  });
}

export function useCWV(projectId: string) {
  return useQuery({
    queryKey: ["cwv", projectId],
    queryFn: () => api.seoAdvanced.getCWV(projectId),
    enabled: !!projectId,
  });
}

export function useRunCWV() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId, url, strategy }: { projectId: string; url: string; strategy?: "mobile" | "desktop" }) =>
      api.seoAdvanced.runCWV(projectId, url, strategy),
    onSuccess: (_, { projectId }) => qc.invalidateQueries({ queryKey: ["cwv", projectId] }),
  });
}

export function useKeywordIdeas(projectId: string, seed?: string, match_type?: string) {
  return useQuery({
    queryKey: ["keywordIdeas", projectId, seed, match_type],
    queryFn: () => api.seoAdvanced.getKeywordIdeas(projectId, { seed, match_type, limit: 200 }),
    enabled: !!projectId,
  });
}

export function useKeywordMagic() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId, payload }: { projectId: string; payload: { seed: string; location?: string; include_questions?: boolean; limit?: number } }) =>
      api.seoAdvanced.keywordMagic(projectId, payload),
    onSuccess: (_, { projectId }) => qc.invalidateQueries({ queryKey: ["keywordIdeas", projectId] }),
  });
}

export function useAnalyzeSerp() {
  return useMutation({
    mutationFn: ({ projectId, keyword, location, device }: { projectId: string; keyword: string; location?: string; device?: string }) =>
      api.seoAdvanced.analyzeSerp(projectId, keyword, location, device),
  });
}

export function useAnchors(projectId: string) {
  return useQuery({
    queryKey: ["anchors", projectId],
    queryFn: () => api.seoAdvanced.getAnchors(projectId),
    enabled: !!projectId,
  });
}

export function useRefreshAnchors() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId }: { projectId: string }) => api.seoAdvanced.refreshAnchors(projectId),
    onSuccess: (_, { projectId }) => qc.invalidateQueries({ queryKey: ["anchors", projectId] }),
  });
}

export function useToxic(projectId: string) {
  return useQuery({
    queryKey: ["toxic", projectId],
    queryFn: () => api.seoAdvanced.getToxic(projectId),
    enabled: !!projectId,
  });
}

export function useScanToxic() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId, minScore }: { projectId: string; minScore?: number }) =>
      api.seoAdvanced.scanToxic(projectId, minScore),
    onSuccess: (_, { projectId }) => qc.invalidateQueries({ queryKey: ["toxic", projectId] }),
  });
}

export function useDisavowToxic() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId, toxicId }: { projectId: string; toxicId: string }) =>
      api.seoAdvanced.disavowToxic(projectId, toxicId),
    onSuccess: (_, { projectId }) => qc.invalidateQueries({ queryKey: ["toxic", projectId] }),
  });
}

export function useLinkIntersect() {
  return useMutation({
    mutationFn: ({ projectId }: { projectId: string }) => api.seoAdvanced.intersect(projectId),
  });
}

export function useBriefs(projectId: string) {
  return useQuery({
    queryKey: ["briefs", projectId],
    queryFn: () => api.seoAdvanced.listBriefs(projectId),
    enabled: !!projectId,
  });
}

export function useCreateBrief() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId, payload }: { projectId: string; payload: { target_keyword: string; competitors?: string[]; target_word_count?: number } }) =>
      api.seoAdvanced.createBrief(projectId, payload),
    onSuccess: (_, { projectId }) => qc.invalidateQueries({ queryKey: ["briefs", projectId] }),
  });
}

export function useOptimizeContent() {
  return useMutation({
    mutationFn: ({ projectId, payload }: { projectId: string; payload: { target_keyword: string; content: string; url?: string } }) =>
      api.seoAdvanced.optimize(projectId, payload),
  });
}

export function useTopicClusters(projectId: string) {
  return useQuery({
    queryKey: ["topicClusters", projectId],
    queryFn: () => api.seoAdvanced.listClusters(projectId),
    enabled: !!projectId,
  });
}

export function useBuildCluster() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId, pillar }: { projectId: string; pillar: string }) =>
      api.seoAdvanced.buildCluster(projectId, pillar),
    onSuccess: (_, { projectId }) => qc.invalidateQueries({ queryKey: ["topicClusters", projectId] }),
  });
}

export function useCitations(projectId: string) {
  return useQuery({
    queryKey: ["citations", projectId],
    queryFn: () => api.seoAdvanced.getCitations(projectId),
    enabled: !!projectId,
  });
}

export function useConsistency(projectId: string) {
  return useQuery({
    queryKey: ["consistency", projectId],
    queryFn: () => api.seoAdvanced.getConsistency(projectId),
    enabled: !!projectId,
  });
}

export function useLocalGrid(projectId: string, keyword?: string) {
  return useQuery({
    queryKey: ["localGrid", projectId, keyword],
    queryFn: () => api.seoAdvanced.getGrid(projectId, keyword),
    enabled: !!projectId,
  });
}

export function useRunLocalGrid() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId, params }: { projectId: string; params: { keyword: string; center_lat: number; center_lng: number; radius_km?: number; grid_size?: number } }) =>
      api.seoAdvanced.runGrid(projectId, params),
    onSuccess: (_, { projectId }) => qc.invalidateQueries({ queryKey: ["localGrid", projectId] }),
  });
}

export function useLogEvents(projectId: string, bot?: string) {
  return useQuery({
    queryKey: ["logs", projectId, bot],
    queryFn: () => api.seoAdvanced.getLogs(projectId, bot),
    enabled: !!projectId,
  });
}

export function useUploadLogFile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId, file }: { projectId: string; file: File }) =>
      api.seoAdvanced.uploadLog(projectId, file),
    onSuccess: (_, { projectId }) => qc.invalidateQueries({ queryKey: ["logs", projectId] }),
  });
}

export function useReports(projectId: string) {
  return useQuery({
    queryKey: ["reports", projectId],
    queryFn: () => api.seoAdvanced.listReports(projectId),
    enabled: !!projectId,
  });
}

export function useGenerateReport() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId, payload }: { projectId: string; payload: { report_type: string; title: string; branding?: any } }) =>
      api.seoAdvanced.generateReport(projectId, payload),
    onSuccess: (_, { projectId }) => qc.invalidateQueries({ queryKey: ["reports", projectId] }),
  });
}

// ============================================================================
// SEO gap-fill hooks
// ============================================================================
export function useCannibalization(projectId: string, severity?: string) {
  return useQuery({
    queryKey: ["cannibalization", projectId, severity],
    queryFn: () => api.seoExtra.listCannibalization(projectId, severity),
    enabled: !!projectId,
  });
}

export function useScanCannibalization() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId, payload }: { projectId: string; payload?: { rows?: any[]; min_pages?: number } }) =>
      api.seoExtra.scanCannibalization(projectId, payload),
    onSuccess: (_, { projectId }) => qc.invalidateQueries({ queryKey: ["cannibalization", projectId] }),
  });
}

export function useInternalLinks(projectId: string, target?: string) {
  return useQuery({
    queryKey: ["internal-links", projectId, target],
    queryFn: () => api.seoExtra.listInternalLinks(projectId, target),
    enabled: !!projectId,
  });
}

export function useOrphanPages(projectId: string) {
  return useQuery({
    queryKey: ["orphan-pages", projectId],
    queryFn: () => api.seoExtra.listOrphanPages(projectId),
    enabled: !!projectId,
  });
}

export function useAnalyzeInternalLinks() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId, urls }: { projectId: string; urls: string[] }) =>
      api.seoExtra.analyzeInternalLinks(projectId, urls),
    onSuccess: (_, { projectId }) => {
      qc.invalidateQueries({ queryKey: ["internal-links", projectId] });
      qc.invalidateQueries({ queryKey: ["orphan-pages", projectId] });
    },
  });
}

export function useDomainCompareHistory(projectId: string) {
  return useQuery({
    queryKey: ["domain-compare", projectId],
    queryFn: () => api.seoExtra.domainCompareHistory(projectId),
    enabled: !!projectId,
  });
}

export function useCompareDomains() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId, primary, competitors }: { projectId: string; primary: string; competitors: string[] }) =>
      api.seoExtra.compareDomains(projectId, primary, competitors),
    onSuccess: (_, { projectId }) => qc.invalidateQueries({ queryKey: ["domain-compare", projectId] }),
  });
}

export function useBulkJobs(projectId: string) {
  return useQuery({
    queryKey: ["bulk-jobs", projectId],
    queryFn: () => api.seoExtra.listBulkJobs(projectId),
    enabled: !!projectId,
  });
}

export function useBulkItems(projectId: string, jobId: string | null) {
  return useQuery({
    queryKey: ["bulk-items", projectId, jobId],
    queryFn: () => api.seoExtra.getBulkItems(projectId, jobId!),
    enabled: !!projectId && !!jobId,
  });
}

export function useRunBulk() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId, urls, job_type }: { projectId: string; urls: string[]; job_type?: "onpage" | "cwv" }) =>
      api.seoExtra.runBulk(projectId, urls, job_type ?? "onpage"),
    onSuccess: (_, { projectId }) => qc.invalidateQueries({ queryKey: ["bulk-jobs", projectId] }),
  });
}

export function useGenerateSitemap() {
  return useMutation({
    mutationFn: ({ projectId, payload }: { projectId: string; payload: { urls: any[]; default_changefreq?: string; default_priority?: number } }) =>
      api.seoExtra.generateSitemap(projectId, payload),
  });
}

export function useValidateRobots() {
  return useMutation({
    mutationFn: ({ projectId, payload }: { projectId: string; payload: { url?: string; raw_content?: string } }) =>
      api.seoExtra.validateRobots(projectId, payload),
  });
}

export function useGenerateSchema() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId, payload }: { projectId: string; payload: { schema_type: string; name: string; inputs: any } }) =>
      api.seoExtra.generateSchema(projectId, payload),
    onSuccess: (_, { projectId }) => qc.invalidateQueries({ queryKey: ["schema-templates", projectId] }),
  });
}

export function useSchemaTemplates(projectId: string) {
  return useQuery({
    queryKey: ["schema-templates", projectId],
    queryFn: () => api.seoExtra.listSchemaTemplates(projectId),
    enabled: !!projectId,
  });
}

export function useCampaigns(projectId: string) {
  return useQuery({
    queryKey: ["outreach-campaigns", projectId],
    queryFn: () => api.seoExtra.listCampaigns(projectId),
    enabled: !!projectId,
  });
}

export function useCreateCampaign() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId, payload }: { projectId: string; payload: { name: string; goal?: string; target_link_count?: number } }) =>
      api.seoExtra.createCampaign(projectId, payload),
    onSuccess: (_, { projectId }) => qc.invalidateQueries({ queryKey: ["outreach-campaigns", projectId] }),
  });
}

export function useProspects(projectId: string, campaignId: string | null) {
  return useQuery({
    queryKey: ["prospects", projectId, campaignId],
    queryFn: () => api.seoExtra.listProspects(projectId, campaignId!),
    enabled: !!projectId && !!campaignId,
  });
}

export function useCreateProspect() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId, campaignId, payload }: { projectId: string; campaignId: string; payload: any }) =>
      api.seoExtra.createProspect(projectId, campaignId, payload),
    onSuccess: (_, { projectId, campaignId }) =>
      qc.invalidateQueries({ queryKey: ["prospects", projectId, campaignId] }),
  });
}

export function useUpdateProspect() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId, prospectId, payload }: { projectId: string; prospectId: string; payload: any }) =>
      api.seoExtra.updateProspect(projectId, prospectId, payload),
    onSuccess: (_, { projectId }) => qc.invalidateQueries({ queryKey: ["prospects", projectId] }),
  });
}

export function useSnippetWatch(projectId: string) {
  return useQuery({
    queryKey: ["snippets", projectId],
    queryFn: () => api.seoExtra.listSnippets(projectId),
    enabled: !!projectId,
  });
}

export function useCheckSnippet() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId, keyword }: { projectId: string; keyword: string }) =>
      api.seoExtra.checkSnippet(projectId, keyword),
    onSuccess: (_, { projectId }) => qc.invalidateQueries({ queryKey: ["snippets", projectId] }),
  });
}

export function usePAA(projectId: string, seed?: string) {
  return useQuery({
    queryKey: ["paa", projectId, seed],
    queryFn: () => api.seoExtra.listPAA(projectId, seed),
    enabled: !!projectId,
  });
}

export function useVolatility(projectId: string, direction?: "up" | "down") {
  return useQuery({
    queryKey: ["volatility", projectId, direction],
    queryFn: () => api.seoExtra.listVolatility(projectId, direction),
    enabled: !!projectId,
  });
}

export function useScanVolatility() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId, rank_diffs, drop_threshold, rise_threshold }: { projectId: string; rank_diffs: any[]; drop_threshold?: number; rise_threshold?: number }) =>
      api.seoExtra.scanVolatility(projectId, rank_diffs, drop_threshold, rise_threshold),
    onSuccess: (_, { projectId }) => qc.invalidateQueries({ queryKey: ["volatility", projectId] }),
  });
}

// --- Competitive Intelligence Hooks ---

export function useTrafficAnalytics(domain: string | null) {
  return useQuery({
    queryKey: ["competitive", "traffic", domain],
    queryFn: () => (domain ? api.seoCompetitive.getTraffic(domain) : Promise.reject("No domain provided")),
    enabled: !!domain,
  });
}

export function useCompetitorPPC(domain: string | null) {
  return useQuery({
    queryKey: ["competitive", "ppc", domain],
    queryFn: () => (domain ? api.seoCompetitive.getPPC(domain) : Promise.reject("No domain provided")),
    enabled: !!domain,
  });
}

export function useBrandMonitor(projectId: string) {
  return useQuery({
    queryKey: ["competitive", "brand", projectId],
    queryFn: () => api.seoCompetitive.getBrandMentions(projectId),
    enabled: !!projectId,
  });
}

export function useContentExplorer(query: string | null) {
  return useQuery({
    queryKey: ["competitive", "content", query],
    queryFn: () => (query ? api.seoCompetitive.exploreContent(query) : Promise.reject("No query provided")),
    enabled: !!query,
  });
}

