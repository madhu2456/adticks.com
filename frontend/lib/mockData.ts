// ============================================================
// Mock data for development / demo when API is not connected
// ============================================================
import {
  VisibilityScore, DashboardStats, ChannelPerformance, ActivityItem,
  Keyword, ContentGap, OnPageAudit, TechnicalCheck, AIPromptResult,
  AIVisibilityScore, SOVData, CategoryBreakdown, GSCQuery, GSCMetrics,
  AdCampaign, AdsPerformance, Insight, Recommendation, ScoreHistory,
} from "./types";

export const mockScore: VisibilityScore = {
  overall: 72,
  seo: 78,
  ai: 34,
  gsc: 81,
  ads: 65,
  computed_at: new Date().toISOString(),
};

export const mockStats: DashboardStats = {
  total_keywords: 1284,
  keywords_change: 12,
  ai_mentions: 247,
  ai_mentions_change: -3,
  gsc_impressions: 84320,
  gsc_impressions_change: 18,
  ad_spend: 4280,
  ad_spend_change: -6,
};

export const mockChannelPerformance: ChannelPerformance[] = [
  { channel: "SEO", this_week: 78, last_week: 71 },
  { channel: "AI", this_week: 34, last_week: 29 },
  { channel: "GSC", this_week: 81, last_week: 76 },
  { channel: "Ads", this_week: 65, last_week: 68 },
];

export const mockActivity: ActivityItem[] = [
  {
    id: "1",
    type: "scan",
    title: "Full visibility scan completed",
    description: "Scanned 1,284 keywords across 4 channels",
    timestamp: new Date(Date.now() - 1000 * 60 * 23).toISOString(),
  },
  {
    id: "2",
    type: "ai_scan",
    title: "AI visibility scan finished",
    description: "Tested 48 prompts across ChatGPT, Gemini, and Claude",
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
  },
  {
    id: "3",
    type: "insight",
    title: "3 new P1 insights generated",
    description: "Critical issues found in AI and Ads channels",
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 5).toISOString(),
  },
  {
    id: "4",
    type: "gsc_sync",
    title: "GSC data synced",
    description: "Last 28 days of search console data imported",
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 12).toISOString(),
  },
  {
    id: "5",
    type: "keyword_added",
    title: "47 keywords discovered",
    description: "New keyword opportunities added to tracking",
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
  },
];

export const mockScoreHistory: ScoreHistory[] = Array.from({ length: 30 }, (_, i) => {
  const date = new Date();
  date.setDate(date.getDate() - (29 - i));
  return {
    date: date.toISOString().split("T")[0],
    overall: 55 + Math.floor(Math.random() * 25),
    seo: 60 + Math.floor(Math.random() * 20),
    ai: 20 + Math.floor(Math.random() * 20),
    gsc: 65 + Math.floor(Math.random() * 20),
    ads: 50 + Math.floor(Math.random() * 25),
  };
});

export const mockKeywords: Keyword[] = [
  { id: "1", keyword: "visibility intelligence platform", intent: "informational", difficulty: 42, volume: 1200, position: 3, position_change: 2, project_id: "p1", created_at: new Date().toISOString() },
  { id: "2", keyword: "ai seo tools", intent: "commercial", difficulty: 68, volume: 8900, position: 7, position_change: -1, project_id: "p1", created_at: new Date().toISOString() },
  { id: "3", keyword: "best rank tracking software", intent: "transactional", difficulty: 55, volume: 4400, position: 12, position_change: 3, project_id: "p1", created_at: new Date().toISOString() },
  { id: "4", keyword: "seo dashboard", intent: "navigational", difficulty: 71, volume: 6700, position: 18, position_change: -2, project_id: "p1", created_at: new Date().toISOString() },
  { id: "5", keyword: "keyword difficulty checker", intent: "informational", difficulty: 38, volume: 3300, position: 5, position_change: 1, project_id: "p1", created_at: new Date().toISOString() },
  { id: "6", keyword: "buy seo software", intent: "transactional", difficulty: 62, volume: 2800, position: 21, position_change: 0, project_id: "p1", created_at: new Date().toISOString() },
  { id: "7", keyword: "chatgpt seo optimization", intent: "informational", difficulty: 29, volume: 5500, position: 2, position_change: 4, project_id: "p1", created_at: new Date().toISOString() },
  { id: "8", keyword: "ai content visibility", intent: "commercial", difficulty: 45, volume: 1900, position: 9, position_change: -3, project_id: "p1", created_at: new Date().toISOString() },
];

export const mockContentGaps: ContentGap[] = [
  { id: "1", topic: "AI response optimization", estimated_volume: 12400, competitor_coverage: 4, opportunity_score: 92, keywords: ["llm optimization", "ai seo", "chatgpt visibility"] },
  { id: "2", topic: "Competitor share of voice analysis", estimated_volume: 8700, competitor_coverage: 3, opportunity_score: 87, keywords: ["sov analysis", "brand share of voice", "competitor mentions"] },
  { id: "3", topic: "Technical SEO for JavaScript apps", estimated_volume: 6200, competitor_coverage: 5, opportunity_score: 74, keywords: ["js seo", "react seo", "next.js seo"] },
  { id: "4", topic: "Google Search Console API integration", estimated_volume: 4100, competitor_coverage: 2, opportunity_score: 81, keywords: ["gsc api", "search console data", "gsc integration"] },
];

export const mockOnPageAudit: OnPageAudit = {
  url: "https://adticks.io",
  overall_score: 78,
  items: [
    { check: "Title Tag", status: "pass", message: "Title tag present and within 60 characters", score: 100 },
    { check: "Meta Description", status: "warning", message: "Meta description is 168 characters — consider shortening to under 160", score: 70 },
    { check: "H1 Tag", status: "pass", message: "Single H1 tag found with target keyword", score: 100 },
    { check: "Image Alt Attributes", status: "fail", message: "7 images missing alt attributes", score: 30 },
    { check: "Page Speed", status: "pass", message: "LCP: 1.8s — Good", score: 90 },
    { check: "Mobile Friendly", status: "pass", message: "Page passes mobile-friendly test", score: 100 },
    { check: "Canonical Tag", status: "pass", message: "Canonical URL correctly set", score: 100 },
    { check: "Schema Markup", status: "warning", message: "No Organization schema detected", score: 50 },
    { check: "Internal Links", status: "pass", message: "14 internal links found", score: 85 },
    { check: "HTTPS", status: "pass", message: "Site served over HTTPS", score: 100 },
  ],
  audited_at: new Date().toISOString(),
};

export const mockTechnicalChecks: TechnicalCheck[] = [
  { check: "HTTPS Enabled", status: "pass", description: "All pages served over HTTPS" },
  { check: "robots.txt", status: "pass", description: "robots.txt found and valid" },
  { check: "XML Sitemap", status: "pass", description: "Sitemap found at /sitemap.xml with 142 URLs" },
  { check: "Core Web Vitals", status: "warning", description: "CLS score 0.14 — needs improvement", fix: "Specify image dimensions to prevent layout shifts" },
  { check: "Crawl Errors", status: "fail", description: "23 pages returning 404 errors", fix: "Set up 301 redirects for moved content" },
  { check: "Duplicate Content", status: "warning", description: "3 pages have duplicate meta descriptions" },
  { check: "Page Speed (Mobile)", status: "pass", description: "Average mobile score: 82/100" },
  { check: "Structured Data", status: "warning", description: "Schema errors found on 5 pages", fix: "Fix JSON-LD structured data errors" },
];

export const mockAIScore: AIVisibilityScore = {
  score: 34,
  total_prompts: 48,
  prompts_appeared_in: 16,
  avg_position: 2.3,
  computed_at: new Date().toISOString(),
};

export const mockSOV: SOVData[] = [
  { brand: "AdTicks", mention_count: 47, percentage: 22, is_self: true },
  { brand: "Semrush", mention_count: 82, percentage: 39, is_self: false },
  { brand: "Ahrefs", mention_count: 54, percentage: 26, is_self: false },
  { brand: "Moz", mention_count: 27, percentage: 13, is_self: false },
];

export const mockCategoryBreakdown: CategoryBreakdown[] = [
  { category: "Brand Queries", score: 58, total: 12 },
  { category: "Comparison", score: 29, total: 18 },
  { category: "Problem-Based", score: 41, total: 10 },
  { category: "Feature Queries", score: 22, total: 8 },
];

export const mockAIResults: AIPromptResult[] = [
  {
    id: "1",
    prompt: { id: "p1", prompt: "What are the best SEO tools in 2024?", category: "comparison", project_id: "proj1" },
    llm: "chatgpt",
    mentions: [
      { brand: "Semrush", position: 1, mentioned: true },
      { brand: "Ahrefs", position: 2, mentioned: true },
      { brand: "AdTicks", position: 3, mentioned: true },
    ],
    scanned_at: new Date().toISOString(),
  },
  {
    id: "2",
    prompt: { id: "p2", prompt: "How can I track my website's AI visibility?", category: "problem", project_id: "proj1" },
    llm: "gemini",
    mentions: [
      { brand: "AdTicks", position: 1, mentioned: true },
      { brand: "Semrush", position: 2, mentioned: true },
    ],
    scanned_at: new Date().toISOString(),
  },
  {
    id: "3",
    prompt: { id: "p3", prompt: "Best visibility intelligence platforms for agencies", category: "comparison", project_id: "proj1" },
    llm: "claude",
    mentions: [
      { brand: "Semrush", position: 1, mentioned: true },
      { brand: "Ahrefs", position: 2, mentioned: true },
      { brand: "Moz", position: 3, mentioned: true },
    ],
    scanned_at: new Date().toISOString(),
  },
];

export const mockGSCMetrics: GSCMetrics[] = Array.from({ length: 28 }, (_, i) => {
  const date = new Date();
  date.setDate(date.getDate() - (27 - i));
  return {
    date: date.toISOString().split("T")[0],
    clicks: 800 + Math.floor(Math.random() * 600),
    impressions: 28000 + Math.floor(Math.random() * 8000),
    ctr: 2.5 + Math.random() * 1.5,
    position: 14 + Math.random() * 6,
  };
});

export const mockGSCQueries: GSCQuery[] = [
  { query: "visibility intelligence platform", clicks: 342, impressions: 4800, ctr: 7.1, position: 3.2 },
  { query: "ai seo tools comparison", clicks: 218, impressions: 6200, ctr: 3.5, position: 7.8 },
  { query: "best seo dashboard 2024", clicks: 196, impressions: 5100, ctr: 3.8, position: 6.1 },
  { query: "chatgpt seo optimization guide", clicks: 187, impressions: 3900, ctr: 4.8, position: 4.5 },
  { query: "rank tracking software free", clicks: 164, impressions: 8700, ctr: 1.9, position: 12.3 },
  { query: "seo keyword difficulty tool", clicks: 142, impressions: 4200, ctr: 3.4, position: 8.9 },
  { query: "content gap analysis tool", clicks: 128, impressions: 3600, ctr: 3.6, position: 9.2 },
  { query: "ai brand mentions monitoring", clicks: 112, impressions: 2100, ctr: 5.3, position: 5.7 },
];

export const mockCampaigns: AdCampaign[] = [
  { id: "1", name: "Brand Awareness - Q3", status: "active", budget: 1500, spend: 1247, impressions: 182000, clicks: 3640, conversions: 48, cpc: 0.34, roas: 4.2, ctr: 2.0 },
  { id: "2", name: "Competitor Conquest", status: "active", budget: 1000, spend: 892, impressions: 94000, clicks: 1880, conversions: 31, cpc: 0.47, roas: 3.8, ctr: 2.0 },
  { id: "3", name: "Retargeting - Trial Users", status: "active", budget: 800, spend: 756, impressions: 62000, clicks: 2170, conversions: 67, cpc: 0.35, roas: 6.1, ctr: 3.5 },
  { id: "4", name: "Product Launch - AI Features", status: "paused", budget: 2000, spend: 1380, impressions: 145000, clicks: 4060, conversions: 29, cpc: 0.34, roas: 2.9, ctr: 2.8 },
];

export const mockAdsPerformance: AdsPerformance[] = Array.from({ length: 30 }, (_, i) => {
  const date = new Date();
  date.setDate(date.getDate() - (29 - i));
  return {
    date: date.toISOString().split("T")[0],
    spend: 120 + Math.floor(Math.random() * 60),
    impressions: 15000 + Math.floor(Math.random() * 5000),
    clicks: 300 + Math.floor(Math.random() * 150),
    conversions: 4 + Math.floor(Math.random() * 6),
    cpc: 0.3 + Math.random() * 0.25,
    roas: 3.0 + Math.random() * 2.5,
  };
});

export const mockInsights: Insight[] = [
  {
    id: "1",
    title: "Brand missing from 66% of AI responses",
    description: "In 32 out of 48 AI prompts tested, your brand was not mentioned. Competitors Semrush and Ahrefs appear in 80%+ of the same prompts.",
    category: "ai",
    priority: "P1",
    data_snippet: "AI visibility score: 34% vs industry avg 61%",
    action_label: "View AI Visibility",
    action_url: "/ai-visibility",
    created_at: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
    is_read: false,
  },
  {
    id: "2",
    title: "23 pages returning 404 errors",
    description: "Crawl detected 23 broken pages that may be losing link equity and harming crawl budget. These pages still receive organic traffic from GSC data.",
    category: "seo",
    priority: "P1",
    data_snippet: "Estimated traffic loss: ~340 clicks/month",
    action_label: "View Technical SEO",
    action_url: "/seo?tab=technical",
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 3).toISOString(),
    is_read: false,
  },
  {
    id: "3",
    title: "Ad spend efficiency declining",
    description: "Campaign 'Product Launch - AI Features' has a ROAS of 2.9 — below the 3.5 target. Consider pausing underperforming ad groups.",
    category: "ads",
    priority: "P2",
    data_snippet: "Current ROAS: 2.9 | Target: 3.5",
    action_label: "View Ads",
    action_url: "/ads",
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 6).toISOString(),
    is_read: false,
  },
  {
    id: "4",
    title: "High-opportunity content gap detected",
    description: "'AI response optimization' has 12,400 monthly searches with only 4 competitors covering it. This is a prime content opportunity.",
    category: "seo",
    priority: "P2",
    data_snippet: "Volume: 12,400/mo | Opportunity score: 92/100",
    action_label: "View Content Gaps",
    action_url: "/seo?tab=gaps",
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 8).toISOString(),
    is_read: true,
  },
  {
    id: "5",
    title: "GSC impressions up 18% week-over-week",
    description: "Organic impressions increased from 71,400 to 84,320. Top movers: 'chatgpt seo optimization' (+240%), 'ai brand mentions' (+180%).",
    category: "gsc",
    priority: "P3",
    data_snippet: "Impressions: 84,320 (+18% WoW)",
    action_label: "View GSC",
    action_url: "/gsc",
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 12).toISOString(),
    is_read: true,
  },
];

export const mockRecommendations: Recommendation[] = [
  { id: "1", title: "Create AI-optimized FAQ content", description: "Publish comprehensive FAQ pages targeting the 32 prompts where your brand is not mentioned", priority: "P1", category: "ai", effort: "medium", impact: "high" },
  { id: "2", title: "Fix 404 errors with 301 redirects", description: "Map broken URLs to the closest live page to recover lost link equity", priority: "P1", category: "seo", effort: "low", impact: "high" },
  { id: "3", title: "Pause underperforming ad groups", description: "Pause ad groups with ROAS below 2.5 in the Product Launch campaign", priority: "P2", category: "ads", effort: "low", impact: "medium" },
  { id: "4", title: "Write 'AI response optimization' guide", description: "Target this 12K volume topic with a comprehensive pillar page", priority: "P2", category: "seo", effort: "high", impact: "high" },
  { id: "5", title: "Add Organization schema markup", description: "Implement JSON-LD Organization schema to improve brand knowledge panel", priority: "P3", category: "seo", effort: "low", impact: "medium" },
];
