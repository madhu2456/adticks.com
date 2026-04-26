"use client";
import React from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
  Search, Bot, BarChart2, DollarSign,
  TrendingUp, TrendingDown, ArrowUpRight, ArrowRight,
  Zap, Sparkles, RefreshCw, Clock, ChevronRight,
  BarChart, Activity, Target, Globe,
} from "lucide-react";
import { VisibilityScore } from "@/components/dashboard/VisibilityScore";
import { ChannelBreakdown } from "@/components/dashboard/ChannelBreakdown";
import { TopInsights } from "@/components/dashboard/TopInsights";
import { RecentActivity } from "@/components/dashboard/RecentActivity";
import { Skeleton } from "@/components/ui/skeleton";
import { formatNumber, formatCurrency, cn } from "@/lib/utils";
import { useActiveProject } from "@/hooks/useProject";
import { useInsights } from "@/hooks/useInsights";
import { useAlertModal } from "@/hooks/useAlertModal";
import { getUser } from "@/lib/auth";
import { api } from "@/lib/api";
import { ScanProgressModal } from "@/components/projects/ScanProgressModal";
import { 
  mockStats, mockScore, mockChannelPerformance, 
  mockActivity, mockInsights 
} from "@/lib/mockData";

/* ── Mini sparkline SVG ──────────────────────────────────────────────── */
function Sparkline({
  data, color, positive, width = 72, height = 32,
}: {
  data: number[];
  color: string;
  positive: boolean;
  width?: number;
  height?: number;
}) {
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const pts = data.map((v, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((v - min) / range) * (height - 4) - 2;
    return `${x},${y}`;
  });
  const pathD = `M ${pts.join(" L ")}`;
  const fillD = `M ${pts[0]} L ${pts.join(" L ")} L ${width},${height} L 0,${height} Z`;

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} fill="none">
      <defs>
        <linearGradient id={`sg-${color.replace("#","")}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.25" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={fillD} fill={`url(#sg-${color.replace("#","")})`} />
      <path d={pathD} stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/* ── Sparkline data seeds ────────────────────────────────────────────── */
const SPARKLINES: Record<string, number[]> = {
  total_keywords:  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  ai_mentions:     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  gsc_impressions: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  ad_spend:        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
};

/* ── Stat card config ────────────────────────────────────────────────── */
const STAT_CARDS = [
  {
    label: "Total Keywords",
    sublabel: "tracked positions",
    key: "total_keywords" as const,
    change_key: "keywords_change" as const,
    icon: Search,
    color: "#6366f1",
    bgColor: "rgba(99,102,241,0.1)",
    format: (v: number) => formatNumber(v, true),
    href: "/seo",
  },
  {
    label: "AI Mentions",
    sublabel: "across LLMs",
    key: "ai_mentions" as const,
    change_key: "ai_mentions_change" as const,
    icon: Bot,
    color: "#8b5cf6",
    bgColor: "rgba(139,92,246,0.1)",
    format: (v: number) => formatNumber(v, true),
    href: "/aeo",
  },
  {
    label: "GSC Impressions",
    sublabel: "last 28 days",
    key: "gsc_impressions" as const,
    change_key: "gsc_impressions_change" as const,
    icon: BarChart2,
    color: "#3b82f6",
    bgColor: "rgba(59,130,246,0.1)",
    format: (v: number) => formatNumber(v, true),
    href: "/gsc",
  },
  {
    label: "Ad Spend",
    sublabel: "this month",
    key: "ad_spend" as const,
    change_key: "ad_spend_change" as const,
    icon: DollarSign,
    color: "#f97316",
    bgColor: "rgba(249,115,22,0.1)",
    format: (v: number) => formatCurrency(v),
    href: "/ads",
  },
];

/* ── Quick actions ───────────────────────────────────────────────────── */
const QUICK_ACTIONS = [
  { label: "SEO Report",       icon: BarChart,  color: "#6366f1", href: "/seo",          desc: "Export rankings" },
  { label: "AI Scan",          icon: Sparkles,  color: "#8b5cf6", href: "/aeo", desc: "Check LLM mentions" },
  { label: "GSC Insights",     icon: Activity,  color: "#3b82f6", href: "/gsc",           desc: "Search analytics" },
  { label: "Campaign Perf.",   icon: Target,    color: "#f97316", href: "/ads",            desc: "Ad performance" },
];

/* ── Greeting ─────────────────────────────────────────────────────────── */
function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 17) return "Good afternoon";
  return "Good evening";
}

export function DashboardContent() {
  const { activeProject } = useActiveProject();
  const [user, setUser] = React.useState<any>(null);

  React.useEffect(() => {
    setUser(getUser());
  }, []);

  const projectId = activeProject?.id || "";
  
  // Fetch real data from backend
  const { data: scoreData, isLoading: scoreLoading } = useQuery({
    queryKey: ["dashboard-score", projectId],
    queryFn: async () => {
      if (!projectId) return null;
      try {
        return await api.scores.getLatest(projectId);
      } catch (err: any) {
        // 404 is expected if no scans have been run yet - use fallback data
        if (err.response?.status === 404) {
          return null;
        }
        console.error("Failed to fetch score:", err);
        return null;
      }
    },
    enabled: !!projectId,
  });

  const { data: insightsData, isLoading: insightsLoading } = useInsights(projectId);

  // Use mock data as fallback
  const stats    = { 
    organic_traffic: mockStats.organic_traffic,
    organic_traffic_change: mockStats.organic_traffic_change,
    visibility_score: scoreData?.seo_score || mockStats.visibility_score,
    visibility_score_change: mockStats.visibility_score_change,
    ad_spend: mockStats.ad_spend,
    ad_spend_change: mockStats.ad_spend_change,
  };
  const score    = scoreData || mockScore;
  const channels = mockChannelPerformance;
  const activity = mockActivity;
  const insights = (insightsData as any)?.slice ? (insightsData as any).slice(0, 3) : (insightsData as any)?.data?.slice(0, 3) || mockInsights;

  const greeting = getGreeting();
  const { showAlert, AlertModal } = useAlertModal();

  const [isScanModalOpen, setIsScanModalOpen] = React.useState(false);
  const [activeTaskId, setActiveTaskId] = React.useState<string | null>(null);

  const handleRefresh = async () => {
    if (!activeProject) {
      showAlert({
        title: "Project Required",
        message: "Please select a project first.",
        type: "warning",
        confirmText: "OK",
      });
      return;
    }

    try {
      const data = await api.ai.runScan(activeProject.id);
      setActiveTaskId(data.task_id);
      setIsScanModalOpen(true);
    } catch (err) {
      console.error("Scan error:", err);
      showAlert({
        title: "Scan Failed",
        message: "Failed to start scan. Please try again.",
        type: "error",
        confirmText: "Close",
      });
    }
  };

  if (!activeProject) {
    return (
      <div className="relative flex items-center justify-center min-h-[60vh] p-6 text-center">
        <div className="max-w-md w-full">
          <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-[#6366f1]/20 to-[#8b5cf6]/20 border border-[#6366f1]/30 flex items-center justify-center mx-auto mb-8 shadow-2xl shadow-[#6366f1]/20 animate-pulse">
            <BarChart2 className="h-10 w-10 text-[#6366f1]" />
          </div>
          <h2 className="text-2xl font-bold text-text-1 mb-3 tracking-tight">Your Dashboard is Waiting.</h2>
          <p className="text-text-3 text-sm leading-relaxed mb-10">
            AdTicks needs a project to start analyzing visibility, AI mentions, and search performance. 
            Create your first project to unlock total intelligence.
          </p>
          <div className="p-1 rounded-2xl bg-white/[0.03] border border-white/5 flex flex-col gap-2">
             <div className="flex items-center gap-3 p-3 rounded-xl bg-white/[0.02]">
                <div className="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-400">
                  <Search size={16} />
                </div>
                <div className="text-left">
                   <p className="text-[12px] font-bold text-text-1">Step 1: Create Project</p>
                   <p className="text-[10px] text-text-3">Add your brand name and domain</p>
                </div>
             </div>
             <div className="flex items-center gap-3 p-3 rounded-xl opacity-50">
                <div className="w-8 h-8 rounded-lg bg-violet-500/10 flex items-center justify-center text-violet-400">
                  <Sparkles size={16} />
                </div>
                <div className="text-left">
                   <p className="text-[12px] font-bold text-text-1">Step 2: Connect Channels</p>
                   <p className="text-[10px] text-text-3">Sync GSC and LLM scanning</p>
                </div>
             </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="relative min-h-full">
      {/* ── Background atmosphere ────────────────────────────────────── */}
      <div className="pointer-events-none select-none fixed inset-0 overflow-hidden z-0">
        <div
          className="absolute -top-32 -left-32 w-[600px] h-[600px] rounded-full opacity-[0.06]"
          style={{
            background: 'radial-gradient(circle, #6366f1, transparent 70%)',
            filter: 'blur(60px)',
            animation: 'orbFloat 12s ease-in-out infinite',
          }}
        />
        <div
          className="absolute top-1/3 -right-48 w-[500px] h-[500px] rounded-full opacity-[0.05]"
          style={{
            background: 'radial-gradient(circle, #8b5cf6, transparent 70%)',
            filter: 'blur(60px)',
            animation: 'orbFloat 16s ease-in-out infinite reverse',
          }}
        />
      </div>

      <div className="relative z-10 space-y-6">

        {/* ── Page header ─────────────────────────────────────────────── */}
        <div data-animate-in="1" className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h1 className="text-[22px] font-bold text-text-1 tracking-tight">
                {greeting}, {user?.full_name || user?.name || "User"} 👋
              </h1>
            </div>
            <div className="flex items-center gap-3 text-[13px] text-text-3">
              <span className="flex items-center gap-1.5">
                <Clock size={12} />
                Just now
              </span>
              <span className="w-px h-3.5" style={{ background: 'rgba(255,255,255,0.1)' }} />
              <span className="flex items-center gap-1.5">
                <Globe size={12} />
                {activeProject?.domain || "yourdomain.com"}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-shrink-0">
            <button
              onClick={handleRefresh}
              className="flex items-center gap-1.5 h-8 px-3 rounded-lg text-[13px] font-medium text-text-2 hover:text-text-1 hover:bg-white/[0.05] transition-all"
              style={{ border: '1px solid rgba(255,255,255,0.07)' }}
            >
              <RefreshCw size={13} />
              <span className="hidden sm:inline">Refresh</span>
            </button>
            <Link
              href="/insights"
              className="flex items-center gap-1.5 h-8 px-3 rounded-lg text-[13px] font-semibold transition-all"
              style={{
                background: 'rgba(99,102,241,0.12)',
                color: '#818cf8',
                border: '1px solid rgba(99,102,241,0.2)',
              }}
            >
              <Zap size={13} />
              <span className="hidden sm:inline">0 insights</span>
              <ChevronRight size={12} />
            </Link>
          </div>
        </div>

        {/* ── Quick actions ────────────────────────────────────────────── */}
        <div data-animate-in="2" className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {QUICK_ACTIONS.map((qa) => {
            const Icon = qa.icon;
            return (
              <Link
                key={qa.label}
                href={qa.href}
                className="group flex items-center gap-2.5 h-10 px-3 rounded-xl transition-all hover:-translate-y-px"
                style={{
                  background: 'var(--surface-1)',
                  border: '1px solid var(--border)',
                }}
              >
                <div
                  className="w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0"
                  style={{ background: `${qa.color}18` }}
                >
                  <Icon size={13} style={{ color: qa.color }} />
                </div>
                <div className="min-w-0">
                  <p className="text-[12px] font-medium text-text-2 group-hover:text-text-1 transition-colors truncate">
                    {qa.label}
                  </p>
                  <p className="text-[10px] text-text-3 truncate">{qa.desc}</p>
                </div>
                <ArrowUpRight
                  size={12}
                  className="text-text-3 ml-auto opacity-0 group-hover:opacity-100 -translate-x-1 group-hover:translate-x-0 transition-all flex-shrink-0"
                />
              </Link>
            );
          })}
        </div>

        {/* ── Top row: Visibility Score + Stat cards ────────────────────── */}
        <div data-animate-in="3" className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          {/* Visibility score — 2 cols */}
          <div className="lg:col-span-2">
            <VisibilityScore score={score} />
          </div>

          {/* Stat cards — 2×2 grid */}
          <div className="lg:col-span-2 grid grid-cols-2 gap-4">
            {STAT_CARDS.map((card, idx) => {
              const value  = (stats as any)[card.key];
              const change = (stats as any)[card.change_key];
              const positive = change >= 0;
              const Icon     = card.icon;
              const sparkData = SPARKLINES[card.key];
              return (
                <Link href={card.href} key={card.key}>
                  <div
                    className="relative overflow-hidden rounded-xl h-full cursor-pointer group transition-all hover:-translate-y-px"
                    style={{
                      background: 'var(--surface-2)',
                      border: '1px solid var(--border)',
                      boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
                    }}
                  >
                    {/* Hover border glow */}
                    <div
                      className="absolute inset-0 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"
                      style={{
                        boxShadow: `inset 0 0 0 1px ${card.color}30`,
                      }}
                    />

                    <div className="p-4">
                      <div className="flex items-start justify-between mb-2">
                        <div
                          className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                          style={{ background: card.bgColor }}
                        >
                          <Icon size={15} style={{ color: card.color }} />
                        </div>
                        <div
                          className={cn(
                            "flex items-center gap-0.5 text-[11px] font-semibold px-1.5 py-0.5 rounded-md",
                            positive
                              ? "text-success bg-success/10"
                              : "text-danger bg-danger/10",
                          )}
                        >
                          {positive
                            ? <TrendingUp size={10} />
                            : <TrendingDown size={10} />}
                          {change}%
                        </div>
                      </div>

                      <p className="text-[22px] font-bold text-text-1 tabular-nums leading-none mb-0.5">
                        {card.format(value)}
                      </p>
                      <p className="text-[11px] font-medium text-text-2">{card.label}</p>
                      <p className="text-[10px] text-text-3">{card.sublabel}</p>

                      {/* Sparkline */}
                      <div className="mt-3 -mb-1 -mx-1">
                        <Sparkline
                          data={sparkData}
                          color={card.color}
                          positive={positive}
                          width={76}
                          height={28}
                        />
                      </div>
                    </div>

                    {/* Corner decoration */}
                    <div
                      className="absolute bottom-0 right-0 w-16 h-16 rounded-full -mr-6 -mb-6 pointer-events-none"
                      style={{
                        background: `radial-gradient(circle, ${card.color}20, transparent 70%)`,
                      }}
                    />
                  </div>
                </Link>
              );
            })}
          </div>
        </div>

        {/* ── Channel Performance + Activity ───────────────────────────── */}
        <div data-animate-in="4" className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2">
            <ChannelBreakdown data={channels} />
          </div>
          <div>
            <RecentActivity items={activity} />
          </div>
        </div>

        {/* ── Top Insights ────────────────────────────────────────────── */}
        <div data-animate-in="5">
          <TopInsights insights={insights} />
        </div>

      </div>
      {AlertModal}
      <ScanProgressModal
        projectId={projectId}
        taskId={activeTaskId}
        isOpen={isScanModalOpen}
        onClose={() => setIsScanModalOpen(false)}
        onComplete={() => {
          setIsScanModalOpen(false);
          window.location.reload();
        }}
      />
    </div>
  );
}
