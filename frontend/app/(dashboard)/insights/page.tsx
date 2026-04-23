"use client";
import React, { useState, useMemo } from "react";
import { RefreshCw, AlertTriangle, TrendingUp, Search } from "lucide-react";
import { InsightList } from "@/components/insights/InsightList";
import { RecommendationPanel } from "@/components/insights/RecommendationPanel";
import { Insight, InsightCategory, InsightPriority } from "@/lib/types";

type CategoryFilter = "all" | InsightCategory;
type PriorityFilter = "all" | InsightPriority;
type StatusFilter = "all" | "new" | "reviewed";

function isNew(createdAt: string) {
  return Date.now() - new Date(createdAt).getTime() < 1000 * 60 * 60 * 24;
}

export default function InsightsPage() {
  const [insights, setInsights] = useState<Insight[]>(mockInsights);
  const [category, setCategory] = useState<CategoryFilter>("all");
  const [priority, setPriority] = useState<PriorityFilter>("all");
  const [status, setStatus] = useState<StatusFilter>("all");
  const [refreshing, setRefreshing] = useState(false);

  function handleMarkRead(id: string) {
    setInsights((prev) =>
      prev.map((ins) => (ins.id === id ? { ...ins, is_read: true } : ins))
    );
  }

  function handleRefresh() {
    setRefreshing(true);
    setTimeout(() => setRefreshing(false), 1800);
  }

  const filtered = useMemo(() => {
    return insights.filter((ins) => {
      if (category !== "all" && ins.category !== category) return false;
      if (priority !== "all" && ins.priority !== priority) return false;
      if (status === "new" && (ins.is_read || !isNew(ins.created_at))) return false;
      if (status === "reviewed" && !ins.is_read) return false;
      return true;
    });
  }, [insights, category, priority, status]);

  const criticalCount = insights.filter((i) => i.priority === "P1").length;
  const highCount = insights.filter((i) => i.priority === "P2").length;
  const opportunityCount = insights.filter((i) => i.priority === "P3").length;

  const catButtons: { value: CategoryFilter; label: string }[] = [
    { value: "all", label: "All" },
    { value: "seo", label: "SEO" },
    { value: "ai", label: "AI Visibility" },
    { value: "gsc", label: "GSC" },
    { value: "ads", label: "Ads" },
    { value: "cross-channel", label: "Cross-Channel" },
  ];

  const priButtons: { value: PriorityFilter; label: string }[] = [
    { value: "all", label: "All" },
    { value: "P1", label: "P1 Critical" },
    { value: "P2", label: "P2 High" },
    { value: "P3", label: "P3 Medium" },
  ];

  const statusButtons: { value: StatusFilter; label: string }[] = [
    { value: "all", label: "All" },
    { value: "new", label: "New" },
    { value: "reviewed", label: "Reviewed" },
  ];

  function FilterBtn<T extends string>({
    current,
    value,
    label,
    onChange,
  }: {
    current: T;
    value: T;
    label: string;
    onChange: (v: T) => void;
  }) {
    return (
      <button
        onClick={() => onChange(value)}
        className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${
          current === value
            ? "bg-[#6366f1] text-white"
            : "bg-[#334155]/50 text-[#94a3b8] hover:text-[#f1f5f9] hover:bg-[#334155]"
        }`}
      >
        {label}
      </button>
    );
  }

  return (
    <div className="p-6 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#f1f5f9]">Insights &amp; Recommendations</h1>
          <p className="text-sm text-[#94a3b8] mt-1">Last updated 12 mins ago</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 bg-[#6366f1]/10 hover:bg-[#6366f1]/20 border border-[#6366f1]/30 text-[#6366f1] rounded-xl px-4 py-2 text-sm font-medium transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
          {refreshing ? "Refreshing..." : "Refresh Insights"}
        </button>
      </div>

      {/* Summary bar */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="flex items-center gap-2 bg-[#ef4444]/10 border border-[#ef4444]/20 rounded-lg px-4 py-2">
          <AlertTriangle className="h-4 w-4 text-[#ef4444]" />
          <span className="text-sm font-semibold text-[#ef4444]">{criticalCount} Critical</span>
        </div>
        <div className="flex items-center gap-2 bg-[#f97316]/10 border border-[#f97316]/20 rounded-lg px-4 py-2">
          <TrendingUp className="h-4 w-4 text-[#f97316]" />
          <span className="text-sm font-semibold text-[#f97316]">{highCount} High Priority</span>
        </div>
        <div className="flex items-center gap-2 bg-[#10b981]/10 border border-[#10b981]/20 rounded-lg px-4 py-2">
          <Search className="h-4 w-4 text-[#10b981]" />
          <span className="text-sm font-semibold text-[#10b981]">{opportunityCount} Opportunities</span>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-[#1e293b] rounded-xl border border-[#334155] p-4 space-y-3">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-[#94a3b8] font-medium w-16 shrink-0">Category:</span>
          {catButtons.map((b) => (
            <FilterBtn key={b.value} current={category} value={b.value} label={b.label} onChange={setCategory} />
          ))}
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-[#94a3b8] font-medium w-16 shrink-0">Priority:</span>
          {priButtons.map((b) => (
            <FilterBtn key={b.value} current={priority} value={b.value} label={b.label} onChange={setPriority} />
          ))}
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-[#94a3b8] font-medium w-16 shrink-0">Status:</span>
          {statusButtons.map((b) => (
            <FilterBtn key={b.value} current={status} value={b.value} label={b.label} onChange={setStatus} />
          ))}
        </div>
      </div>

      {/* Main content */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2">
          <InsightList insights={filtered} onMarkRead={handleMarkRead} />
        </div>
        <div>
          <RecommendationPanel recommendations={mockRecommendations} />
        </div>
      </div>
    </div>
  );
}

