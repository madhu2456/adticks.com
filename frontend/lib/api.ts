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
    console.log(`[API] Request to ${config.url}, token present: ${!!token}`);
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
    // Explicitly log every API error to the console with details
    const status = error.response?.status;
    const url = error.config?.url;
    const method = error.config?.method?.toUpperCase();
    const errorData = error.response?.data;
    
    console.error(`[API Error] ${method} ${url} | Status: ${status}`, {
      data: errorData,
      message: error.message
    });

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
      axiosInstance.get<{ auth_url: string }>(`/gsc/auth`).then(unwrap),
    completeAuth: (code: string) =>
      axiosInstance.post<{ status: string }>(`/gsc/complete`, { code }).then(unwrap),
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
    getBacklinks: (projectId: string, skip = 0, limit = 50) =>
      axiosInstance.get<PaginatedResponse<any>>(`/seo/projects/${projectId}/backlinks?skip=${skip}&limit=${limit}`).then(unwrap),
    getCompetitorKeywords: (projectId: string, skip = 0, limit = 50) =>
      axiosInstance.get<PaginatedResponse<any>>(`/seo/projects/${projectId}/competitors/keywords?skip=${skip}&limit=${limit}`).then(unwrap),
    getSerpFeatures: (keywordId: string) =>
      axiosInstance.get<any>(`/seo/keywords/${keywordId}/serp-features`).then(unwrap),
  },

  // Cache
  cache: {
    getStats: (projectId: string) =>
      axiosInstance.get<any>(`/cache/stats/${projectId}`).then(unwrap),
    invalidate: (projectId: string) =>
      axiosInstance.post<any>(`/cache/invalidate/${projectId}`).then(unwrap),
    purgeAll: () =>
      axiosInstance.post<any>("/cache/purge-all").then(unwrap),
  },
};

export default axiosInstance;
