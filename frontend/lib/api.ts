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

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8002";

const axiosInstance: AxiosInstance = axios.create({
  baseURL: `${BASE_URL}/api`,
  headers: { "Content-Type": "application/json" },
  timeout: 30000,
});

// Request interceptor — attach JWT
axiosInstance.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
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
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
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
    logout: () => axiosInstance.post("/auth/logout").then(unwrap),
    refreshToken: (refreshToken: string) =>
      axiosInstance.post<AuthTokens>("/auth/refresh", { refresh_token: refreshToken }).then(unwrap),
  },

  // Projects
  projects: {
    list: () => axiosInstance.get<Project[]>("/projects").then(unwrap),
    get: (id: string) => axiosInstance.get<Project>(`/projects/${id}`).then(unwrap),
    create: (data: Partial<Project>) =>
      axiosInstance.post<Project>("/projects", data).then(unwrap),
    update: (id: string, data: Partial<Project>) =>
      axiosInstance.patch<Project>(`/projects/${id}`, data).then(unwrap),
    delete: (id: string) => axiosInstance.delete(`/projects/${id}`).then(unwrap),
  },

  // Scores
  scores: {
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
      axiosInstance.post<{ job_id: string }>(`/seo/${projectId}/keywords/generate`).then(unwrap),
    getKeywords: (projectId: string, page = 1, search?: string) =>
      axiosInstance
        .get<PaginatedResponse<Keyword>>(
          `/seo/${projectId}/keywords?page=${page}${search ? `&search=${search}` : ""}`
        )
        .then(unwrap),
    getRankings: (projectId: string, keywordId: string, days = 30) =>
      axiosInstance
        .get<RankingHistory>(`/seo/${projectId}/keywords/${keywordId}/rankings?days=${days}`)
        .then(unwrap),
    getGaps: (projectId: string) =>
      axiosInstance.get<ContentGap[]>(`/seo/${projectId}/gaps`).then(unwrap),
    runAudit: (projectId: string, url: string) =>
      axiosInstance.post<OnPageAudit>(`/seo/${projectId}/audit`, { url }).then(unwrap),
    getTechnicalChecks: (projectId: string) =>
      axiosInstance.get<TechnicalCheck[]>(`/seo/${projectId}/technical`).then(unwrap),
  },

  // AI Visibility
  ai: {
    generatePrompts: (projectId: string) =>
      axiosInstance.post<{ job_id: string }>(`/ai/${projectId}/prompts/generate`).then(unwrap),
    runScan: (projectId: string) =>
      axiosInstance.post<{ job_id: string }>(`/ai/${projectId}/scan`).then(unwrap),
    getResults: (projectId: string, page = 1) =>
      axiosInstance
        .get<PaginatedResponse<AIPromptResult>>(`/ai/${projectId}/results?page=${page}`)
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
      axiosInstance.get<{ url: string }>(`/gsc/${projectId}/auth-url`).then(unwrap),
    sync: (projectId: string) =>
      axiosInstance.post<{ job_id: string }>(`/gsc/${projectId}/sync`).then(unwrap),
    getQueries: (projectId: string, days = 28) =>
      axiosInstance.get<GSCQuery[]>(`/gsc/${projectId}/queries?days=${days}`).then(unwrap),
    getPages: (projectId: string) =>
      axiosInstance.get<GSCPage[]>(`/gsc/${projectId}/pages`).then(unwrap),
    getMetrics: (projectId: string, days = 28) =>
      axiosInstance.get<GSCMetrics[]>(`/gsc/${projectId}/metrics?days=${days}`).then(unwrap),
  },

  // Ads
  ads: {
    getPerformance: (projectId: string, days = 30) =>
      axiosInstance.get<AdsPerformance[]>(`/ads/${projectId}/performance?days=${days}`).then(unwrap),
    getCampaigns: (projectId: string) =>
      axiosInstance.get<AdCampaign[]>(`/ads/${projectId}/campaigns`).then(unwrap),
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
};

export default axiosInstance;
