import { 
  DashboardStats, VisibilityScore, ChannelPerformance, 
  ActivityItem, Insight, Recommendation, Keyword,
  ContentGap, TechnicalCheck, AIVisibilityScore,
  SOVData, CategoryBreakdown, AIPromptResult,
  AdsPerformance, GSCQuery, GSCMetrics, GSCPage
} from "./types";

export const mockStats: DashboardStats = {
  total_keywords: 2847,
  keywords_change: 12.4,
  ai_mentions: 186,
  ai_mentions_change: 8.2,
  gsc_impressions: 52400,
  gsc_impressions_change: -2.1,
  ad_spend: 4320,
  ad_spend_change: 15.6,
};

export const mockScore: VisibilityScore = {
  overall: 78,
  seo: 82,
  ai: 64,
  gsc: 71,
  ads: 85,
  computed_at: new Date().toISOString(),
};

export const mockChannelPerformance: ChannelPerformance[] = [
  { channel: "Organic Search", this_week: 12400, last_week: 11800 },
  { channel: "AI Results", this_week: 3200, last_week: 2800 },
  { channel: "Google Ads", this_week: 5600, last_week: 5900 },
  { channel: "Social Media", this_week: 2100, last_week: 1950 },
  { channel: "Direct", this_week: 4300, last_week: 4100 },
];

export const mockActivity: ActivityItem[] = [
  { id: "1", type: "ai_scan", title: "AI Scan Completed", description: "Brand mentioned in 85% of prompts.", timestamp: new Date(Date.now() - 3600000).toISOString() },
  { id: "2", type: "keyword_added", title: "New Keywords Tracked", description: "Added 12 new high-volume keywords.", timestamp: new Date(Date.now() - 86400000).toISOString() },
  { id: "3", type: "insight", title: "New Critical Insight", description: "Technical issue detected on /pricing page.", timestamp: new Date(Date.now() - 172800000).toISOString() },
];

export const mockInsights: Insight[] = [
  { id: "ins1", title: "Optimize Title Tags", description: "32 pages have missing or duplicate title tags.", category: "seo", priority: "P1", created_at: new Date().toISOString(), is_read: false },
  { id: "ins2", title: "Brand mention low in AI", description: "Your brand is only mentioned in 5% of comparison prompts.", category: "ai", priority: "P2", created_at: new Date().toISOString(), is_read: false },
];

export const mockRecommendations: Recommendation[] = [
  { id: "rec1", title: "Fix Technical SEO", description: "Address 404 errors found on key landing pages.", priority: "P1", category: "seo", effort: "low", impact: "high" },
  { id: "rec2", title: "Expand AI Content", description: "Create more documentation on feature comparisons.", priority: "P2", category: "ai", effort: "medium", impact: "high" },
];

export const mockKeywords: Keyword[] = [
  { id: "k1", keyword: "seo tools", intent: "commercial", difficulty: 85, volume: 12000, position: 3, position_change: 2, project_id: "p1", created_at: new Date().toISOString() },
  { id: "k2", keyword: "ai visibility", intent: "informational", difficulty: 45, volume: 2400, position: 1, position_change: 0, project_id: "p1", created_at: new Date().toISOString() },
];

export const mockContentGaps: ContentGap[] = [
  { id: "g1", topic: "Technical SEO Audit", estimated_volume: 5000, competitor_coverage: 80, opportunity_score: 85, keywords: ["audit", "checklist"] },
];

export const mockTechnicalChecks: TechnicalCheck[] = [
  { check: "Page Speed", status: "pass", description: "Fast load times across all pages." },
  { check: "Mobile Friendly", status: "pass", description: "Fully responsive design." },
];

export const mockAIScore: AIVisibilityScore = {
  score: 64,
  total_prompts: 120,
  prompts_appeared_in: 77,
  avg_position: 2.4,
  computed_at: new Date().toISOString(),
};

export const mockSOV: SOVData[] = [
  { brand: "AdTicks", mention_count: 85, percentage: 42, is_self: true },
  { brand: "Competitor A", mention_count: 65, percentage: 32, is_self: false },
];

export const mockCategoryBreakdown: CategoryBreakdown[] = [
  { category: "Brand Searches", score: 85, total: 100 },
  { category: "Comparisons", score: 45, total: 100 },
];

export const mockAIResults: AIPromptResult[] = [
  { id: "r1", prompt: { id: "p1", prompt: "What is AdTicks?", category: "brand", project_id: "p1" }, llm: "chatgpt", mentions: [{ brand: "AdTicks", position: 1, mentioned: true }], scanned_at: new Date().toISOString() },
];

export const mockAdsPerformance: AdsPerformance[] = Array.from({ length: 30 }).map((_, i) => ({
  date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toISOString(),
  spend: Math.random() * 100 + 50,
  impressions: Math.random() * 1000 + 2000,
  clicks: Math.random() * 50 + 100,
  conversions: Math.random() * 5 + 1,
  cpc: Math.random() * 2 + 0.5,
  roas: Math.random() * 5 + 2,
}));

export const mockGSCQueries: GSCQuery[] = [
  { query: "seo tools", clicks: 342, impressions: 4800, ctr: 7.1, position: 3.2 },
];

export const mockGSCPages: GSCPage[] = [
  { query: "/", clicks: 489, impressions: 8200, ctr: 6.0, position: 2.8 },
];

export const mockGSCMetrics: GSCMetrics[] = Array.from({ length: 30 }).map((_, i) => ({
  date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toISOString(),
  clicks: Math.floor(Math.random() * 50) + 100,
  impressions: Math.floor(Math.random() * 1000) + 2000,
  ctr: Math.random() * 5 + 2,
  position: Math.random() * 5 + 8,
}));
