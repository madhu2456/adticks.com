"use client";
import React from "react";
import {
  Search, Bot, BarChart2, Megaphone, Layers,
  CheckCircle, ChevronRight, Sparkles,
} from "lucide-react";
import { Insight } from "@/lib/types";

interface InsightCardProps {
  insight: Insight;
  onMarkRead?: (id: string) => void;
}

const PRIORITY_STYLES: Record<string, { border: string; badge: string; label: string }> = {
  P1: { border: "border-l-[#ef4444]", badge: "bg-[#ef4444]/10 text-[#ef4444] border-[#ef4444]/30", label: "P1 CRITICAL" },
  P2: { border: "border-l-[#f97316]", badge: "bg-[#f97316]/10 text-[#f97316] border-[#f97316]/30", label: "P2 HIGH" },
  P3: { border: "border-l-[#f59e0b]", badge: "bg-[#f59e0b]/10 text-[#f59e0b] border-[#f59e0b]/30", label: "P3 MEDIUM" },
  P4: { border: "border-l-[#6366f1]", badge: "bg-[#6366f1]/10 text-[#6366f1] border-[#6366f1]/30", label: "P4 LOW" },
  P5: { border: "border-l-[#475569]", badge: "bg-[#334155] text-[#94a3b8] border-[#475569]/30", label: "P5 INFO" },
};

const CATEGORY_ICONS: Record<string, React.ElementType> = {
  seo: Search,
  ai: Bot,
  gsc: BarChart2,
  ads: Megaphone,
  "cross-channel": Layers,
};

const CATEGORY_LABELS: Record<string, string> = {
  seo: "SEO",
  ai: "AI Visibility",
  gsc: "Search Console",
  ads: "Ads",
  "cross-channel": "Cross-Channel",
};

function isNew(createdAt: string) {
  return Date.now() - new Date(createdAt).getTime() < 1000 * 60 * 60 * 24;
}

export function InsightCard({ insight, onMarkRead }: InsightCardProps) {
  const priority = PRIORITY_STYLES[insight.priority] ?? PRIORITY_STYLES.P5;
  const CategoryIcon = CATEGORY_ICONS[insight.category] ?? Layers;

  return (
    <div
      className={`bg-[#1e293b] rounded-xl border border-[#334155] border-l-4 ${priority.border} p-5 transition-all hover:scale-[1.01] hover:shadow-xl hover:shadow-black/20 group`}
    >
      {/* Top row */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-[#334155] flex items-center justify-center">
            <CategoryIcon className="h-3.5 w-3.5 text-[#94a3b8]" />
          </div>
          <span className="text-xs font-medium text-[#94a3b8]">
            {CATEGORY_LABELS[insight.category]}
          </span>
          {isNew(insight.created_at) && !insight.is_read && (
            <span className="flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-[#6366f1]/10 border border-[#6366f1]/20 text-[10px] font-semibold text-[#6366f1]">
              <Sparkles className="h-2.5 w-2.5" />
              NEW
            </span>
          )}
        </div>
        <span className={`text-[10px] font-bold tracking-wider px-2 py-0.5 rounded border ${priority.badge}`}>
          {priority.label}
        </span>
      </div>

      {/* Title */}
      <h3 className="text-[#f1f5f9] font-semibold text-sm leading-snug mb-2">
        {insight.title}
      </h3>

      {/* Description */}
      <p className="text-xs text-[#94a3b8] leading-relaxed mb-3">
        {insight.description}
      </p>

      {/* Data snippet pills */}
      {insight.data_snippet && (
        <div className="flex flex-wrap gap-1.5 mb-4">
          {insight.data_snippet.split("|").map((pill, i) => (
            <span
              key={i}
              className="px-2 py-0.5 rounded-md bg-[#0f172a] border border-[#334155] text-[11px] text-[#94a3b8] font-mono"
            >
              {pill.trim()}
            </span>
          ))}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2">
        {!insight.is_read && onMarkRead && (
          <button
            onClick={() => onMarkRead(insight.id)}
            className="flex items-center gap-1.5 text-xs text-[#94a3b8] hover:text-[#10b981] transition-colors"
          >
            <CheckCircle className="h-3.5 w-3.5" />
            Mark as read
          </button>
        )}
        {insight.action_label && (
          <a
            href={insight.action_url}
            className="ml-auto flex items-center gap-1 text-xs text-[#6366f1] hover:text-[#8b5cf6] font-medium transition-colors"
          >
            {insight.action_label}
            <ChevronRight className="h-3.5 w-3.5" />
          </a>
        )}
      </div>
    </div>
  );
}
