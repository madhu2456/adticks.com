// ============================================================
// AdTicks — TypeScript interfaces matching backend schemas
// ============================================================

// Auth
export interface User {
  id: string;
  email: string;
  name: string;
  full_name?: string;
  avatar?: string;
  plan: "free" | "starter" | "pro" | "enterprise";
  trial_ends_at?: string;
  created_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name?: string;
}

// Projects
export interface Project {
  id: string;
  name: string;
  brand_name?: string;
  domain: string;
  color?: string;
  initials?: string;
  favicon?: string;
  created_at: string;
  updated_at: string;
  gsc_connected: boolean;
  ads_connected: boolean;
}

// Visibility Scores
export interface VisibilityScore {
  overall: number;
  seo: number;
  ai: number;
  gsc: number;
  ads: number;
  computed_at: string;
}

export interface ScoreHistory {
  date: string;
  overall: number;
  seo: number;
  ai: number;
  gsc: number;
  ads: number;
}

// SEO
export type KeywordIntent = "informational" | "transactional" | "commercial" | "navigational";

export interface Keyword {
  id: string;
  keyword: string;
  intent: KeywordIntent;
  difficulty: number;
  volume: number;
  position: number | null;
  position_change: number;
  url?: string;
  project_id: string;
  created_at: string;
}

export interface RankingDataPoint {
  date: string;
  position: number;
}

export interface RankingHistory {
  keyword: string;
  data: RankingDataPoint[];
}

export interface OnPageAuditItem {
  check: string;
  status: "pass" | "fail" | "warning";
  message: string;
  score: number;
}

export interface OnPageAudit {
  url: string;
  overall_score: number;
  items: OnPageAuditItem[];
  audited_at: string;
}

export interface ContentGap {
  id: string;
  topic: string;
  estimated_volume: number;
  competitor_coverage: number;
  opportunity_score: number;
  keywords: string[];
}

export interface TechnicalCheck {
  check: string;
  status: "pass" | "fail" | "warning";
  description: string;
  fix?: string;
}

// AI Visibility
export interface AIPrompt {
  id: string;
  prompt: string;
  category: "brand" | "comparison" | "problem" | "feature";
  project_id: string;
}

export interface AIBrandMention {
  brand: string;
  position: number;
  mentioned: boolean;
}

export interface AIPromptResult {
  id: string;
  prompt: AIPrompt;
  llm: "chatgpt" | "gemini" | "claude" | "perplexity";
  mentions: AIBrandMention[];
  raw_response?: string;
  scanned_at: string;
}

export interface AIVisibilityScore {
  score: number;
  total_prompts: number;
  prompts_appeared_in: number;
  avg_position: number;
  computed_at: string;
}

export interface SOVData {
  brand: string;
  mention_count: number;
  percentage: number;
  is_self: boolean;
}

export interface CategoryBreakdown {
  category: string;
  score: number;
  total: number;
}

// GSC
export interface GSCQuery {
  query: string;
  clicks: number;
  impressions: number;
  ctr: number;
  position: number;
}

export interface GSCPage {
  query: string;
  clicks: number;
  impressions: number;
  ctr: number;
  position: number;
}

export interface GSCMetrics {
  date: string;
  clicks: number;
  impressions: number;
  ctr: number;
  position: number;
}

// Ads
export interface AdCampaign {
  id: string;
  name: string;
  status: "active" | "paused" | "ended";
  budget: number;
  spend: number;
  impressions: number;
  clicks: number;
  conversions: number;
  cpc: number;
  roas: number;
  ctr: number;
}

export interface AdsPerformance {
  date: string;
  spend: number;
  impressions: number;
  clicks: number;
  conversions: number;
  cpc: number;
  roas: number;
}

// Insights
export type InsightPriority = "P1" | "P2" | "P3";
export type InsightCategory = "seo" | "ai" | "cross-channel" | "ads" | "gsc";

export interface Insight {
  id: string;
  title: string;
  description: string;
  category: InsightCategory;
  priority: InsightPriority;
  data_snippet?: string;
  action_label?: string;
  action_url?: string;
  created_at: string;
  is_read: boolean;
}

export interface InsightsSummary {
  total: number;
  by_priority: { P1: number; P2: number; P3: number };
  by_category: Record<InsightCategory, number>;
}

export interface Recommendation {
  id: string;
  title: string;
  description: string;
  priority: InsightPriority;
  category: InsightCategory;
  effort: "low" | "medium" | "high";
  impact: "low" | "medium" | "high";
}

// Stats
export interface DashboardStats {
  total_keywords: number;
  keywords_change: number;
  ai_mentions: number;
  ai_mentions_change: number;
  gsc_impressions: number;
  gsc_impressions_change: number;
  ad_spend: number;
  ad_spend_change: number;
}

// GEO Module
export interface Location {
  id: string;
  project_id: string;
  name: string;
  address: string;
  city: string;
  state: string;
  country: string;
  postal_code?: string;
  phone?: string;
  latitude?: number;
  longitude?: number;
  google_business_id?: string;
  created_at: string;
  updated_at: string;
}

export interface LocalRank {
  id: string;
  location_id: string;
  keyword_id?: string;
  keyword: string;
  google_maps_rank?: number;
  local_pack_position?: number;
  local_search_rank?: number;
  device: "desktop" | "mobile";
  timestamp: string;
  created_at: string;
}

export interface Review {
  id: string;
  location_id: string;
  source: string;
  external_id?: string;
  rating: number;
  text?: string;
  author: string;
  sentiment_score?: number;
  sentiment_label?: "positive" | "negative" | "neutral";
  review_date?: string;
  verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface ReviewSummary {
  id: string;
  location_id: string;
  total_reviews: number;
  average_rating?: number;
  five_star: number;
  four_star: number;
  three_star: number;
  two_star: number;
  one_star: number;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  google_reviews: number;
  yelp_reviews: number;
  facebook_reviews: number;
  last_updated: string;
  created_at: string;
}

export interface Citation {
  id: string;
  location_id: string;
  source_name: string;
  url: string;
  consistency_score: number;
  name_match: boolean;
  address_match: boolean;
  phone_match: boolean;
  business_name?: string;
  citation_address?: string;
  citation_phone?: string;
  last_verified?: string;
  created_at: string;
  updated_at: string;
}

export interface NAPCheckResult {
  location_id: string;
  total_citations: number;
  consistent_citations: number;
  consistency_percentage: number;
  issues: Array<{
    citation_id: string;
    source: string;
    url: string;
    issues: string[];
  }>;
}

export interface ChannelPerformance {
  channel: string;
  this_week: number;
  last_week: number;
}

// Activity
export interface ActivityItem {
  id: string;
  type: "scan" | "keyword_added" | "insight" | "gsc_sync" | "ai_scan";
  title: string;
  description: string;
  timestamp: string;
  icon?: string;
}

// API Response wrappers
export interface ApiResponse<T> {
  data: T;
  error: string | null;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  skip: number;
  limit: number;
  has_more: boolean;
}
