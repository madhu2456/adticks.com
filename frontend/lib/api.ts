import axios, { AxiosInstance, AxiosResponse } from "axios";
import { getAccessToken, clearTokens, setTokens, getRefreshToken } from "./auth";
import {
  AuthTokens, User, Project, VisibilityScore, ScoreHistory,
  Keyword, RankingHistory, OnPageAudit, ContentGap, TechnicalCheck,
  AIPromptResult, AIVisibilityScore, SOVData, CategoryBreakdown,
  GSCQuery, GSCPage, GSCMetrics, AdCampaign, AdsPerformance,
  Insight, InsightsSummary, Recommendation, DashboardStats,
  ChannelPerformance, ActivityItem, LoginRequest, RegisterRequest,
  PaginatedResponse, ApiResponse,
  TrafficAnalyticsResponse, PPCResearchResponse, BrandMonitorResponse, ContentExplorerResponse,
  DomainOverviewResponse, BulkKeywordResponse,
} from "./types";

// Use relative URL when frontend and backend are on same domain (production)
// Use explicit URL for local development
const getBaseUrl = () => {
  let apiUrl = "";
  if (typeof window === "undefined") {
    apiUrl = process.env.NEXT_PUBLIC_API_URL || "https://adticks.com";
  } else {
    apiUrl = process.env.NEXT_PUBLIC_API_URL || "";
    
    // In browser: if we're on HTTPS and the API URL hasn't been set, use relative path
    if (!apiUrl && window.location.protocol === "https:") {
      return "";
    }
    
    if (!apiUrl) apiUrl = "https://adticks.com";
  }
  
  // Normalize: remove trailing slash and /api if present, we'll add /api cleanly
  return apiUrl.replace(/\/+$/, "").replace(/\/api$/, "");
};

const BASE_URL = getBaseUrl();

const axiosInstance: AxiosInstance = axios.create({
  baseURL: `${BASE_URL}/api`,
  headers: { "Content-Type": "application/json" },
  timeout: 30000,
});

// Request interceptor — attach JWT
axiosInstance.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    // Only log API requests in development
    if (process.env.NODE_ENV === "development") {
      console.log(`[API] Request to ${config.url}, token present: ${!!token}`);
    }
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor — handle 401 / token refresh
axiosInstance.interceptors.response.use(
  (response) => response,
  async (error) => {
    // Only log errors in development or if they are significant
    if (process.env.NODE_ENV === "development") {
      const status = error.response?.status;
      const url = error.config?.url;
      const method = error.config?.method?.toUpperCase();
      const errorData = error.response?.data;
      
      console.error(`[API Error] ${method} ${url} | Status: ${status}`, {
        data: errorData,
        message: error.message
      });
    }

    const originalRequest = error.config;
    const isLoginRequest = originalRequest.url?.includes("/auth/login");
    
    if (error.response?.status === 401 && !originalRequest._retry && !isLoginRequest) {
      originalRequest._retry = true;
      const refreshToken = getRefreshToken();
      if (refreshToken) {
        try {
          const { data } = await axios.post<AuthTokens>(
            `${BASE_URL}/api/auth/refresh`,
            { refresh_token: refreshToken }
          );
          setTokens(data);
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
          return axiosInstance(originalRequest);
        } catch {
          clearTokens();
          window.location.href = "/login";
        }
      } else {
        clearTokens();
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

function unwrap<T>(response: AxiosResponse<T>): T {
  return response.data;
}

// ============================================================
// API client
// ============================================================
export const api = {
  // Auth
  auth: {
    login: (data: LoginRequest) =>
      axiosInstance.post<AuthTokens>("/auth/login", data).then(unwrap),
    register: (data: RegisterRequest) =>
      axiosInstance.post<AuthTokens>("/auth/register", data).then(unwrap),
    me: () => axiosInstance.get<User>("/auth/me").then(unwrap),
    getUsage: () => axiosInstance.get<any>("/auth/usage").then(unwrap),
    upgrade: () => axiosInstance.post<any>("/auth/upgrade").then(unwrap),
    updateMe: (data: { full_name?: string; email?: string; password?: string; company_name?: string }) =>
      axiosInstance.patch<User>("/auth/me", data).then(unwrap),
    uploadAvatar: (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      return axiosInstance.post<User>("/auth/avatar", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      }).then(unwrap);
    },
    logout: () => axiosInstance.post("/auth/logout").then(unwrap),
    refreshToken: (refreshToken: string) =>
      axiosInstance.post<AuthTokens>("/auth/refresh", { refresh_token: refreshToken }).then(unwrap),
  },

  // Projects
  projects: {
    list: () =>
      axiosInstance
        .get<PaginatedResponse<Project>>("/projects")
        .then(unwrap)
        .then((res) => res.data),
    get: (id: string) => axiosInstance.get<Project>(`/projects/${id}`).then(unwrap),
    create: (data: Partial<Project>) =>
      axiosInstance.post<Project>("/projects", data).then(unwrap),
    update: (id: string, data: Partial<Project>) =>
      axiosInstance.put<Project>(`/projects/${id}`, data).then(unwrap),
    delete: (id: string) => axiosInstance.delete(`/projects/${id}`).then(unwrap),
  },

  // Scores
  scores: {
    getLatest: (projectId: string) =>
      axiosInstance.get<VisibilityScore>(`/scores/${projectId}`).then(unwrap),
    getCurrent: (projectId: string) =>
      axiosInstance.get<VisibilityScore>(`/scores/${projectId}/current`).then(unwrap),
    getHistory: (projectId: string, days = 30) =>
      axiosInstance.get<ScoreHistory[]>(`/scores/${projectId}/history?days=${days}`).then(unwrap),
    getDashboardStats: (projectId: string) =>
      axiosInstance.get<DashboardStats>(`/scores/${projectId}/stats`).then(unwrap),
    getChannelPerformance: (projectId: string) =>
      axiosInstance.get<ChannelPerformance[]>(`/scores/${projectId}/channels`).then(unwrap),
    getActivity: (projectId: string) =>
      axiosInstance.get<ActivityItem[]>(`/scores/${projectId}/activity`).then(unwrap),
  },

  // SEO
  seo: {
    generateKeywords: (projectId: string) =>
      axiosInstance.post<{ task_id: string }>(`/seo/keywords?project_id=${projectId}`).then(unwrap),
    getKeywords: (projectId: string, page = 1, search?: string) =>
      axiosInstance
        .get<PaginatedResponse<Keyword>>(
          `/seo/rankings/${projectId}?skip=${(page - 1) * 50}&limit=50`
        )
        .then(unwrap),
    getRankings: (projectId: string, days = 30) =>
      axiosInstance
        .get<PaginatedResponse<Keyword>>(`/seo/rankings/${projectId}?skip=0&limit=100`)
        .then(unwrap),
    getGaps: (projectId: string) =>
      axiosInstance.get(`/seo/gaps/${projectId}`).then(unwrap),
    getOnPageAudit: (projectId: string) =>
      axiosInstance.get(`/seo/onpage/${projectId}`).then(unwrap),
    runAudit: (projectId: string, url: string) =>
      axiosInstance.post<{ task_id: string }>(`/seo/audit?project_id=${projectId}`, { url }).then(unwrap),
    runOnPageAudit: (projectId: string, url: string) =>
      axiosInstance.post<{ task_id: string }>(`/seo/audit/onpage?project_id=${projectId}&url=${encodeURIComponent(url)}`).then(unwrap),
    runTechnicalAudit: (projectId: string) =>
      axiosInstance.post<{ task_id: string }>(`/seo/audit/technical?project_id=${projectId}`).then(unwrap),
    runGapSync: (projectId: string) =>
      axiosInstance.post<{ task_id: string }>(`/seo/gaps/sync?project_id=${projectId}`).then(unwrap),
    runGscKeywordSync: (projectId: string) =>
      axiosInstance.post<{ task_id: string }>(`/seo/keywords/sync-gsc?project_id=${projectId}`).then(unwrap),
    getTechnicalChecks: (projectId: string) =>
      axiosInstance.get(`/seo/technical/${projectId}`).then(unwrap),
    getAuditHistory: (projectId: string) =>
      axiosInstance.get<any[]>(`/seo/projects/${projectId}/audit/history`).then(unwrap),
    getSOV: (projectId: string) =>
      axiosInstance.get<any>(`/seo/sov/${projectId}`).then(unwrap),
  },

  // Clusters
  clusters: {
    list: (projectId: string, skip = 0, limit = 50) =>
      axiosInstance.get<PaginatedResponse<any>>(`/projects/${projectId}/clusters?skip=${skip}&limit=${limit}`).then(unwrap),
    get: (projectId: string, clusterId: string) =>
      axiosInstance.get<any>(`/projects/${projectId}/clusters/${clusterId}`).then(unwrap),
    create: (projectId: string, data: { topic_name: string; keywords: string[] }) =>
      axiosInstance.post<any>(`/projects/${projectId}/clusters`, data).then(unwrap),
    update: (projectId: string, clusterId: string, data: { topic_name?: string; keywords?: string[] }) =>
      axiosInstance.put<any>(`/projects/${projectId}/clusters/${clusterId}`, data).then(unwrap),
    delete: (projectId: string, clusterId: string) =>
      axiosInstance.delete(`/projects/${projectId}/clusters/${clusterId}`).then(unwrap),
  },

  // AI Visibility
  ai: {
    generatePrompts: (projectId: string) =>
      axiosInstance.post<{ task_id: string; status: string }>(`/prompts/generate?project_id=${projectId}`).then(unwrap),
    runScan: (projectId: string) =>
      axiosInstance.post<{ task_id: string; status: string }>(`/scan/run?project_id=${projectId}`).then(unwrap),
    getTaskStatus: (taskId: string) =>
      axiosInstance.get<{ task_id: string; status: string; result?: unknown; error?: string }>(`/scan/status/${taskId}`).then(unwrap),
    getResults: (projectId: string, skip = 0, limit = 50) =>
      axiosInstance
        .get<PaginatedResponse<AIPromptResult>>(`/results/${projectId}?skip=${skip}&limit=${limit}`)
        .then(unwrap),
    getScore: (projectId: string) =>
      axiosInstance.get<AIVisibilityScore>(`/ai/${projectId}/score`).then(unwrap),
    getSOV: (projectId: string) =>
      axiosInstance.get<SOVData[]>(`/ai/${projectId}/sov`).then(unwrap),
    getCategoryBreakdown: (projectId: string) =>
      axiosInstance.get<CategoryBreakdown[]>(`/ai/${projectId}/categories`).then(unwrap),
    getMentions: (projectId: string) =>
      axiosInstance.get<AIPromptResult[]>(`/ai/${projectId}/mentions`).then(unwrap),
  },

  // GSC
  gsc: {
    getAuthUrl: (projectId: string) =>
      axiosInstance.get<{ auth_url: string; state: string; pkce_state: string }>(`/gsc/auth`).then(unwrap),
    completeAuth: (code: string, state?: string, pkce_state?: string) =>
      axiosInstance.post<{ status: string }>(`/gsc/complete`, { code, state, pkce_state }).then(unwrap),
    listProperties: () =>
      axiosInstance.get<any[]>(`/gsc/properties`).then(unwrap),
    connectProperty: (projectId: string, propertyUrl: string) =>
      axiosInstance.post<{ status: string }>(`/gsc/connect/${projectId}?property_url=${encodeURIComponent(propertyUrl)}`).then(unwrap),
    sync: (projectId: string) =>
      axiosInstance.post<{ status: string; task_id: string }>(`/gsc/sync/${projectId}`).then(unwrap),
    getQueries: (projectId: string, days = 28) =>
      axiosInstance.get<PaginatedResponse<GSCQuery>>(`/gsc/queries/${projectId}?skip=0&limit=100`).then(unwrap),
    getPages: (projectId: string) =>
      axiosInstance.get<PaginatedResponse<GSCQuery>>(`/gsc/queries/${projectId}?skip=0&limit=100`).then(unwrap),
    getMetrics: (projectId: string, days = 28) =>
      axiosInstance.get<PaginatedResponse<GSCQuery>>(`/gsc/queries/${projectId}?skip=0&limit=100`).then(unwrap),
  },

  // Ads
  ads: {
    sync: (projectId: string) =>
      axiosInstance.post<{ status: string; task_id: string }>(`/ads/sync/${projectId}`).then(unwrap),
    getPerformance: (projectId: string, days = 30) =>
      axiosInstance.get<PaginatedResponse<AdsPerformance>>(`/ads/performance/${projectId}?skip=0&limit=100`).then(unwrap),
    getCampaigns: (projectId: string) =>
      axiosInstance.get<PaginatedResponse<AdCampaign>>(`/ads/performance/${projectId}?skip=0&limit=100`).then(unwrap),
  },

  // Insights
  insights: {
    getInsights: (projectId: string, category?: string, priority?: string) =>
      axiosInstance
        .get<Insight[]>(
          `/insights/${projectId}?${category ? `category=${category}&` : ""}${priority ? `priority=${priority}` : ""}`
        )
        .then(unwrap),
    getSummary: (projectId: string) =>
      axiosInstance.get<InsightsSummary>(`/insights/${projectId}/summary`).then(unwrap),
    refresh: (projectId: string) =>
      axiosInstance.post<{ job_id: string }>(`/insights/${projectId}/refresh`).then(unwrap),
    getRecommendations: (projectId: string) =>
      axiosInstance.get<Recommendation[]>(`/insights/${projectId}/recommendations`).then(unwrap),
    markRead: (insightId: string) =>
      axiosInstance.patch(`/insights/${insightId}/read`).then(unwrap),
  },

  // Geo / Local SEO
  geo: {
    getLocations: (projectId: string) =>
      axiosInstance.get<PaginatedResponse<any>>(`/geo/projects/${projectId}/locations`).then(unwrap),
    createLocation: (projectId: string, data: any) =>
      axiosInstance.post<any>(`/geo/projects/${projectId}/locations`, data).then(unwrap),
    getLocation: (locationId: string) =>
      axiosInstance.get<any>(`/geo/locations/${locationId}`).then(unwrap),
    updateLocation: (locationId: string, data: any) =>
      axiosInstance.put<any>(`/geo/locations/${locationId}`, data).then(unwrap),
    deleteLocation: (locationId: string) =>
      axiosInstance.delete(`/geo/locations/${locationId}`).then(unwrap),
    getRanks: (locationId: string) =>
      axiosInstance.get<PaginatedResponse<any>>(`/geo/locations/${locationId}/ranks`).then(unwrap),
    getReviews: (locationId: string) =>
      axiosInstance.get<PaginatedResponse<any>>(`/geo/locations/${locationId}/reviews`).then(unwrap),
    getReviewSummary: (locationId: string) =>
      axiosInstance.get<any>(`/geo/locations/${locationId}/reviews/summary`).then(unwrap),
    getCitations: (locationId: string) =>
      axiosInstance.get<PaginatedResponse<any>>(`/geo/locations/${locationId}/citations`).then(unwrap),
    getNapCheck: (locationId: string) =>
      axiosInstance.get<any>(`/geo/locations/${locationId}/citations/nap-check`).then(unwrap),
  },

  // AEO / AI SEO
  aeo: {
    getSummary: (projectId: string) =>
      axiosInstance.get<any>(`/aeo/projects/${projectId}/visibility/summary`).then(unwrap),
    getChatGPT: (projectId: string) =>
      axiosInstance.get<any[]>(`/aeo/projects/${projectId}/visibility/chatgpt`).then(unwrap),
    getPerplexity: (projectId: string) =>
      axiosInstance.get<any[]>(`/aeo/projects/${projectId}/visibility/perplexity`).then(unwrap),
    getClaude: (projectId: string) =>
      axiosInstance.get<any[]>(`/aeo/projects/${projectId}/visibility/claude`).then(unwrap),
    getSnippetSummary: (projectId: string) =>
      axiosInstance.get<any>(`/aeo/projects/${projectId}/snippets/summary`).then(unwrap),
    getSnippets: (keywordId: string) =>
      axiosInstance.get<any[]>(`/aeo/keywords/${keywordId}/snippets`).then(unwrap),
    getPAA: (keywordId: string) =>
      axiosInstance.get<any[]>(`/aeo/keywords/${keywordId}/paa`).then(unwrap),
    getRecommendations: (projectId: string) =>
      axiosInstance.get<any[]>(`/aeo/projects/${projectId}/recommendations`).then(unwrap),
    getFAQs: (projectId: string) =>
      axiosInstance.get<any[]>(`/aeo/projects/${projectId}/faqs`).then(unwrap),
    approveFAQ: (faqId: string) =>
      axiosInstance.put<any>(`/aeo/faqs/${faqId}/approve`).then(unwrap),
    checkAIVisibility: (keywordId: string, models: string[]) =>
      axiosInstance.post<any>(`/aeo/check-visibility`, { keyword_id: keywordId, ai_models: models }).then(unwrap),
    updateRecommendation: (recId: string, action: "implemented" | "rejected") =>
      axiosInstance.put<any>(`/aeo/recommendations/${recId}`, { user_action: action }).then(unwrap),
    generateFAQFromPAA: (keywordId: string, paaId: string) =>
      axiosInstance.post<any>(`/aeo/faq/generate-from-paa?keyword_id=${keywordId}&paa_id=${paaId}`).then(unwrap),
    generateFAQ: (projectId: string, keywordId: string) =>
      axiosInstance.post<any>(`/aeo/generate-faq`, { project_id: projectId, keyword_id: keywordId }).then(unwrap),
  },

  // Advanced SEO Suite
  seoSuite: {
    getBacklinks: (projectId: string, skip = 0, limit = 50, minAuthority?: number) =>
      axiosInstance.get<PaginatedResponse<any>>(`/seo/projects/${projectId}/backlinks?skip=${skip}&limit=${limit}${minAuthority ? `&min_authority=${minAuthority}` : ''}`).then(unwrap),
    getBacklinkStats: (projectId: string) =>
      axiosInstance.get<any>(`/seo/projects/${projectId}/backlinks/stats`).then(unwrap),
    getBacklinkIntersect: (projectId: string) =>
      axiosInstance.get<any[]>(`/seo/projects/${projectId}/backlinks/intersect`).then(unwrap),
    getCompetitorKeywords: (projectId: string, skip = 0, limit = 50) =>
      axiosInstance.get<PaginatedResponse<any>>(`/seo/projects/${projectId}/competitors/keywords?skip=${skip}&limit=${limit}`).then(unwrap),
    getSerpFeatures: (keywordId: string) =>
      axiosInstance.get<any>(`/seo/keywords/${keywordId}/serp-features`).then(unwrap),
    getRankHistory: (projectId: string, keywordId?: string, days = 30, skip = 0, limit = 50, device?: string) =>
      axiosInstance.get<PaginatedResponse<any>>(`/seo/projects/${projectId}/keywords/history?days=${days}&skip=${skip}&limit=${limit}${keywordId ? `&keyword_id=${keywordId}` : ''}${device ? `&device=${device}` : ''}`).then(unwrap),
  },

  // Advanced SEO — superset of Ahrefs / SEMrush / Moz features
  seoAdvanced: {
    // Site Audit
    runAudit: (projectId: string, url: string, max_pages = 50, max_depth = 3) =>
      axiosInstance.post<any>(`/seo/projects/${projectId}/audit/run`, { url, max_pages, max_depth }).then(unwrap),
    getAuditSummary: (projectId: string) =>
      axiosInstance.get<any>(`/seo/projects/${projectId}/audit/summary`).then(unwrap),
    getAuditIssues: (projectId: string, params?: { severity?: string; category?: string; urls?: string[]; limit?: number }) => {
      const qs = new URLSearchParams();
      if (params?.severity) qs.set("severity", params.severity);
      if (params?.category) qs.set("category", params.category);
      if (params?.urls && params.urls.length > 0) {
        params.urls.forEach(u => qs.append("urls", u));
      }
      if (params?.limit) qs.set("limit", String(params.limit));
      return axiosInstance.get<any[]>(`/seo/projects/${projectId}/audit/issues?${qs}`).then(unwrap);
    },
    getCrawledPages: (projectId: string, limit = 100) =>
      axiosInstance.get<any[]>(`/seo/projects/${projectId}/audit/pages?limit=${limit}`).then(unwrap),
    getSchemas: (projectId: string) =>
      axiosInstance.get<any[]>(`/seo/projects/${projectId}/audit/schemas`).then(unwrap),

    // Core Web Vitals
    runCWV: (projectId: string, url: string, strategy: "mobile" | "desktop" = "mobile") =>
      axiosInstance.post<any>(`/seo/projects/${projectId}/cwv/run?url=${encodeURIComponent(url)}&strategy=${strategy}`).then(unwrap),
    getCWV: (projectId: string, limit = 20) =>
      axiosInstance.get<any[]>(`/seo/projects/${projectId}/cwv?limit=${limit}`).then(unwrap),

    // Keyword Magic
    keywordMagic: (projectId: string, payload: { seed: string; location?: string; include_questions?: boolean; limit?: number }) =>
      axiosInstance.post<any[]>(`/seo/projects/${projectId}/keyword-magic`, payload).then(unwrap),
    getKeywordIdeas: (projectId: string, params?: { seed?: string; match_type?: string; limit?: number }) => {
      const qs = new URLSearchParams();
      if (params?.seed) qs.set("seed", params.seed);
      if (params?.match_type) qs.set("match_type", params.match_type);
      if (params?.limit) qs.set("limit", String(params.limit));
      return axiosInstance.get<any[]>(`/seo/projects/${projectId}/keyword-magic?${qs}`).then(unwrap);
    },

    // SERP Analyzer
    analyzeSerp: (projectId: string, keyword: string, location = "us", device = "desktop") =>
      axiosInstance.post<any>(`/seo/projects/${projectId}/serp/analyze?keyword=${encodeURIComponent(keyword)}&location=${location}&device=${device}`).then(unwrap),

    // Backlink intelligence
    refreshAnchors: (projectId: string) =>
      axiosInstance.post<any>(`/seo/projects/${projectId}/backlinks/anchors/refresh`).then(unwrap),
    getAnchors: (projectId: string) =>
      axiosInstance.get<any[]>(`/seo/projects/${projectId}/backlinks/anchors`).then(unwrap),
    scanToxic: (projectId: string, minScore = 40) =>
      axiosInstance.post<any>(`/seo/projects/${projectId}/backlinks/toxic/scan?min_score=${minScore}`).then(unwrap),
    getToxic: (projectId: string) =>
      axiosInstance.get<any[]>(`/seo/projects/${projectId}/backlinks/toxic`).then(unwrap),
    disavowToxic: (projectId: string, toxicId: string) =>
      axiosInstance.post<any>(`/seo/projects/${projectId}/backlinks/toxic/${toxicId}/disavow`).then(unwrap),
    exportDisavow: (projectId: string) =>
      axiosInstance.get<{ content: string; format: string }>(`/seo/projects/${projectId}/backlinks/disavow.txt`).then(unwrap),
    intersect: (projectId: string) =>
      axiosInstance.post<any[]>(`/seo/projects/${projectId}/backlinks/intersect`).then(unwrap),

    // Content
    createBrief: (projectId: string, payload: { target_keyword: string; competitors?: string[]; target_word_count?: number }) =>
      axiosInstance.post<any>(`/seo/projects/${projectId}/content/brief`, payload).then(unwrap),
    listBriefs: (projectId: string) =>
      axiosInstance.get<any[]>(`/seo/projects/${projectId}/content/briefs`).then(unwrap),
    optimize: (projectId: string, payload: { target_keyword: string; content: string; url?: string }) =>
      axiosInstance.post<any>(`/seo/projects/${projectId}/content/optimize`, payload).then(unwrap),
    buildCluster: (projectId: string, pillar: string) =>
      axiosInstance.post<any>(`/seo/projects/${projectId}/content/clusters/build?pillar_topic=${encodeURIComponent(pillar)}`).then(unwrap),
    listClusters: (projectId: string) =>
      axiosInstance.get<any[]>(`/seo/projects/${projectId}/content/clusters`).then(unwrap),

    // Local SEO
    getCitations: (projectId: string) =>
      axiosInstance.get<any[]>(`/seo/projects/${projectId}/local/citations`).then(unwrap),
    getConsistency: (projectId: string) =>
      axiosInstance.get<any>(`/seo/projects/${projectId}/local/consistency`).then(unwrap),
    runGrid: (projectId: string, params: { keyword: string; center_lat: number; center_lng: number; radius_km?: number; grid_size?: number }) => {
      const qs = new URLSearchParams();
      qs.set("keyword", params.keyword);
      qs.set("center_lat", String(params.center_lat));
      qs.set("center_lng", String(params.center_lng));
      if (params.radius_km) qs.set("radius_km", String(params.radius_km));
      if (params.grid_size) qs.set("grid_size", String(params.grid_size));
      return axiosInstance.post<any[]>(`/seo/projects/${projectId}/local/grid/run?${qs}`).then(unwrap);
    },
    getGrid: (projectId: string, keyword?: string) =>
      axiosInstance.get<any[]>(`/seo/projects/${projectId}/local/grid${keyword ? `?keyword=${encodeURIComponent(keyword)}` : ""}`).then(unwrap),

    // Logs
    uploadLog: (projectId: string, file: File) => {
      const fd = new FormData();
      fd.append("file", file);
      return axiosInstance.post<any>(`/seo/projects/${projectId}/logs/upload`, fd, {
        headers: { "Content-Type": "multipart/form-data" },
      }).then(unwrap);
    },
    getLogs: (projectId: string, bot?: string) =>
      axiosInstance.get<any[]>(`/seo/projects/${projectId}/logs${bot ? `?bot=${bot}` : ""}`).then(unwrap),

    // Reports
    generateReport: (projectId: string, payload: { report_type: string; title: string; branding?: any }) =>
      axiosInstance.post<any>(`/seo/projects/${projectId}/reports/generate`, payload).then(unwrap),
    listReports: (projectId: string) =>
      axiosInstance.get<any[]>(`/seo/projects/${projectId}/reports`).then(unwrap),

    // Hub overview
    hubOverview: (projectId: string) =>
      axiosInstance.get<any>(`/seo/projects/${projectId}/hub-overview`).then(unwrap),
  },

  // SEO gap-fill (cannibalization, internal links, domain compare, bulk,
  // sitemap/robots/schema generators, outreach, snippet/PAA/volatility)
  seoExtra: {
    // Cannibalization
    scanCannibalization: (projectId: string, payload?: { rows?: any[]; min_pages?: number }) =>
      axiosInstance.post<any[]>(`/seo/projects/${projectId}/cannibalization/scan`, payload || { min_pages: 2 }).then(unwrap),
    listCannibalization: (projectId: string, severity?: string) =>
      axiosInstance.get<any[]>(`/seo/projects/${projectId}/cannibalization${severity ? `?severity=${severity}` : ""}`).then(unwrap),

    // Internal links / orphans
    analyzeInternalLinks: (projectId: string, urls: string[]) =>
      axiosInstance.post<any>(`/seo/projects/${projectId}/internal-links/analyze`, { urls }).then(unwrap),
    listInternalLinks: (projectId: string, target?: string, limit = 200) => {
      const qs = new URLSearchParams();
      qs.set("limit", String(limit));
      if (target) qs.set("target", target);
      return axiosInstance.get<any[]>(`/seo/projects/${projectId}/internal-links?${qs}`).then(unwrap);
    },
    listOrphanPages: (projectId: string) =>
      axiosInstance.get<any[]>(`/seo/projects/${projectId}/orphan-pages`).then(unwrap),

    // Domain comparison
    compareDomains: (projectId: string, primary_domain: string, competitor_domains: string[]) =>
      axiosInstance.post<any>(`/seo/projects/${projectId}/domain-compare`, { primary_domain, competitor_domains }).then(unwrap),
    domainCompareHistory: (projectId: string) =>
      axiosInstance.get<any[]>(`/seo/projects/${projectId}/domain-compare/history`).then(unwrap),

    // Bulk
    runBulk: (projectId: string, urls: string[], job_type: "onpage" | "cwv" = "onpage") =>
      axiosInstance.post<any>(`/seo/projects/${projectId}/bulk/run`, { urls, job_type }).then(unwrap),
    listBulkJobs: (projectId: string) =>
      axiosInstance.get<any[]>(`/seo/projects/${projectId}/bulk`).then(unwrap),
    getBulkItems: (projectId: string, jobId: string) =>
      axiosInstance.get<any[]>(`/seo/projects/${projectId}/bulk/${jobId}/items`).then(unwrap),

    // Sitemap / robots / schema
    generateSitemap: (projectId: string, payload: { urls: any[]; default_changefreq?: string; default_priority?: number }) =>
      axiosInstance.post<any>(`/seo/projects/${projectId}/sitemap/generate`, payload).then(unwrap),
    validateRobots: (projectId: string, payload: { url?: string; raw_content?: string }) =>
      axiosInstance.post<any>(`/seo/projects/${projectId}/robots/validate`, payload).then(unwrap),
    generateSchema: (projectId: string, payload: { schema_type: string; name: string; inputs: any }) =>
      axiosInstance.post<any>(`/seo/projects/${projectId}/schema/generate`, payload).then(unwrap),
    listSchemaTemplates: (projectId: string) =>
      axiosInstance.get<any[]>(`/seo/projects/${projectId}/schema/templates`).then(unwrap),

    // Outreach
    createCampaign: (projectId: string, payload: { name: string; goal?: string; target_link_count?: number }) =>
      axiosInstance.post<any>(`/seo/projects/${projectId}/outreach/campaigns`, payload).then(unwrap),
    listCampaigns: (projectId: string) =>
      axiosInstance.get<any[]>(`/seo/projects/${projectId}/outreach/campaigns`).then(unwrap),
    createProspect: (projectId: string, campaignId: string, payload: any) =>
      axiosInstance.post<any>(`/seo/projects/${projectId}/outreach/campaigns/${campaignId}/prospects`, payload).then(unwrap),
    listProspects: (projectId: string, campaignId: string) =>
      axiosInstance.get<any[]>(`/seo/projects/${projectId}/outreach/campaigns/${campaignId}/prospects`).then(unwrap),
    updateProspect: (projectId: string, prospectId: string, payload: any) =>
      axiosInstance.patch<any>(`/seo/projects/${projectId}/outreach/prospects/${prospectId}`, payload).then(unwrap),
    campaignSummary: (projectId: string, campaignId: string) =>
      axiosInstance.get<any>(`/seo/projects/${projectId}/outreach/campaigns/${campaignId}/summary`).then(unwrap),

    // Featured snippet / PAA / volatility
    listSnippets: (projectId: string) =>
      axiosInstance.get<any[]>(`/seo/projects/${projectId}/snippets`).then(unwrap),
    checkSnippet: (projectId: string, keyword: string) =>
      axiosInstance.post<any>(`/seo/projects/${projectId}/snippets/check?keyword=${encodeURIComponent(keyword)}`).then(unwrap),
    listPAA: (projectId: string, seed?: string) =>
      axiosInstance.get<any[]>(`/seo/projects/${projectId}/paa${seed ? `?seed=${encodeURIComponent(seed)}` : ""}`).then(unwrap),
    scanVolatility: (projectId: string, rank_diffs: any[], drop_threshold = 5, rise_threshold = 5) =>
      axiosInstance.post<any[]>(`/seo/projects/${projectId}/volatility/scan`, { rank_diffs, drop_threshold, rise_threshold }).then(unwrap),
    listVolatility: (projectId: string, direction?: "up" | "down") =>
      axiosInstance.get<any[]>(`/seo/projects/${projectId}/volatility${direction ? `?direction=${direction}` : ""}`).then(unwrap),
  },

  // Competitive Intelligence
  seoCompetitive: {
    getOverview: (domain: string) =>
      axiosInstance.get<DomainOverviewResponse>(`/competitive/overview/${domain}`).then(unwrap),
    getBulkKeywordMetrics: (keywords: string[]) =>
      axiosInstance.post<BulkKeywordResponse>("/competitive/keywords/bulk", { keywords }).then(unwrap),
    getTraffic: (domain: string) =>
      axiosInstance.get<TrafficAnalyticsResponse>(`/competitive/traffic/${domain}`).then(unwrap),
    getPPC: (domain: string) =>
      axiosInstance.get<PPCResearchResponse>(`/competitive/ppc/${domain}`).then(unwrap),
    getBrandMentions: (projectId: string) =>
      axiosInstance.get<BrandMonitorResponse>(`/competitive/brand/${projectId}`).then(unwrap),
    exploreContent: (query: string) =>
      axiosInstance.get<ContentExplorerResponse>(`/competitive/content?q=${encodeURIComponent(query)}`).then(unwrap),
  },

  // Cache
  cache: {
    stats: (projectId: string) =>
      axiosInstance.get<any>(`/cache/stats/${projectId}`).then(unwrap),
    invalidate: (projectId: string) =>
      axiosInstance.post<any>(`/cache/invalidate/${projectId}`).then(unwrap),
    invalidateComponent: (projectId: string, component: string) =>
      axiosInstance.post<any>(`/cache/invalidate-component/${projectId}/${component}`).then(unwrap),
    purgeAll: () =>
      axiosInstance.post<any>("/cache/purge-all").then(unwrap),
    clearDatabase: (projectId: string) =>
      axiosInstance.post<any>(`/cache/clear-db?project_id=${projectId}`).then(unwrap),
  },
};

export default axiosInstance;
