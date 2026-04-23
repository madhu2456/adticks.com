import { 
  DashboardStats, VisibilityScore, ChannelPerformance, 
  ActivityItem, Insight, Recommendation, Keyword,
  ContentGap, TechnicalCheck, AIVisibilityScore,
  SOVData, CategoryBreakdown, AIPromptResult,
  AdsPerformance, GSCQuery, GSCMetrics, GSCPage
} from "./types";

export const mockStats: DashboardStats = {
  total_keywords: 0,
  keywords_change: 0,
  ai_mentions: 0,
  ai_mentions_change: 0,
  gsc_impressions: 0,
  gsc_impressions_change: 0,
  ad_spend: 0,
  ad_spend_change: 0,
};

export const mockScore: VisibilityScore = {
  overall: 0,
  seo: 0,
  ai: 0,
  gsc: 0,
  ads: 0,
  computed_at: new Date().toISOString(),
};

export const mockChannelPerformance: ChannelPerformance[] = [];

export const mockActivity: ActivityItem[] = [];

export const mockInsights: Insight[] = [];

export const mockRecommendations: Recommendation[] = [];

export const mockKeywords: Keyword[] = [];

export const mockContentGaps: ContentGap[] = [];

export const mockTechnicalChecks: TechnicalCheck[] = [];

export const mockAIScore: AIVisibilityScore = {
  score: 0,
  total_prompts: 0,
  prompts_appeared_in: 0,
  avg_position: 0,
  computed_at: new Date().toISOString(),
};

export const mockSOV: SOVData[] = [];

export const mockCategoryBreakdown: CategoryBreakdown[] = [];

export const mockAIResults: AIPromptResult[] = [];

export const mockAdsPerformance: AdsPerformance[] = [];

export const mockGSCQueries: GSCQuery[] = [];

export const mockGSCPages: GSCPage[] = [];

export const mockGSCMetrics: GSCMetrics[] = [];
