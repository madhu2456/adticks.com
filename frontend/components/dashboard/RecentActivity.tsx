"use client";
import React from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { ActivityItem } from "@/lib/types";
import { formatRelativeTime } from "@/lib/utils";
import {
  Scan, Search, Lightbulb, BarChart2, Bot, Plus,
  RefreshCw, TrendingUp, AlertTriangle, Zap,
  CheckCircle2, ChevronRight,
} from "lucide-react";
import Link from "next/link";

/* ── Activity type config ─────────────────────────────────────────────── */
const TYPE_CONFIG: Record<string, {
  icon: React.ElementType;
  color: string;
  bg: string;
  label: string;
}> = {
  scan:         { icon: Scan,        color: "#6366f1", bg: "rgba(99,102,241,0.12)",  label: "Scan" },
  keyword_added:{ icon: Search,      color: "#3b82f6", bg: "rgba(59,130,246,0.12)",  label: "SEO" },
  insight:      { icon: Zap,         color: "#eab308", bg: "rgba(234,179,8,0.12)",   label: "Insight" },
  gsc_sync:     { icon: RefreshCw,   color: "#22c55e", bg: "rgba(34,197,94,0.12)",   label: "GSC" },
  ai_scan:      { icon: Bot,         color: "#8b5cf6", bg: "rgba(139,92,246,0.12)",  label: "AI" },
  alert:        { icon: AlertTriangle,color:"#ef4444", bg: "rgba(239,68,68,0.12)",   label: "Alert" },
  success:      { icon: CheckCircle2,color: "#22c55e", bg: "rgba(34,197,94,0.12)",   label: "Done" },
};

const DEFAULT_TYPE = { icon: Plus, color: "#52525b", bg: "rgba(82,82,91,0.12)", label: "Event" };

interface RecentActivityProps {
  items?: ActivityItem[];
  loading?: boolean;
}

export function RecentActivity({ items, loading }: RecentActivityProps) {
  if (loading) {
    return (
      <div
        className="rounded-xl h-full"
        style={{ background: '#141416', border: '1px solid rgba(255,255,255,0.07)' }}
      >
        <div className="p-5 pb-4"><Skeleton className="h-5 w-36" /></div>
        <div className="px-4 space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="flex gap-3">
              <Skeleton className="h-8 w-8 rounded-xl flex-shrink-0" />
              <div className="flex-1 space-y-1.5">
                <Skeleton className="h-3.5 w-3/4" />
                <Skeleton className="h-3 w-1/2" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  const activityItems = items ?? [];

  return (
    <div
      className="rounded-xl flex flex-col h-full"
      style={{
        background: 'var(--surface-2)',
        border: '1px solid var(--border)',
        boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
      }}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between px-5 py-4 flex-shrink-0"
        style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}
      >
        <div>
          <h3 className="text-[13px] font-semibold text-text-1">Activity</h3>
          <p className="text-[11px] text-text-3 mt-0.5">Recent changes & events</p>
        </div>
        <button className="text-[11px] font-medium text-text-3 hover:text-text-2 flex items-center gap-0.5 transition-colors">
          View all <ChevronRight size={12} />
        </button>
      </div>

      {/* Activity feed */}
      <div className="flex-1 px-4 py-3 overflow-y-auto custom-scroll">
        <div className="relative">
          {activityItems.map((item, i) => {
            const conf = TYPE_CONFIG[item.type] ?? DEFAULT_TYPE;
            const Icon = conf.icon;
            const isLast = i === activityItems.length - 1;

            return (
              <div key={item.id} className="flex gap-3 relative group">
                {/* Timeline connector */}
                {!isLast && (
                  <div
                    className="absolute left-4 top-9 bottom-0 w-px"
                    style={{ background: 'rgba(255,255,255,0.05)' }}
                  />
                )}

                {/* Icon bubble */}
                <div
                  className="relative z-10 w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 transition-transform group-hover:scale-105"
                  style={{
                    background: conf.bg,
                    border: `1px solid ${conf.color}20`,
                  }}
                >
                  <Icon size={13} style={{ color: conf.color }} />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0 pb-4">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className="text-[12px] font-semibold text-text-1 leading-snug">
                        {item.title}
                      </p>
                      <p className="text-[11px] text-text-2 mt-0.5 leading-relaxed">
                        {item.description}
                      </p>
                    </div>
                    {/* Type label */}
                    <span
                      className="flex-shrink-0 text-[9px] font-semibold uppercase tracking-wide px-1.5 py-0.5 rounded-md mt-0.5"
                      style={{
                        background: conf.bg,
                        color: conf.color,
                      }}
                    >
                      {conf.label}
                    </span>
                  </div>
                  <p className="text-[10px] text-text-3 mt-1">
                    {formatRelativeTime(item.timestamp)}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Footer */}
      <div
        className="px-5 py-2.5 flex-shrink-0"
        style={{ borderTop: '1px solid rgba(255,255,255,0.05)', background: 'rgba(0,0,0,0.15)' }}
      >
        <p className="text-[10px] text-text-3 text-center">
          Showing last {activityItems.length} events
        </p>
      </div>
    </div>
  );
}
