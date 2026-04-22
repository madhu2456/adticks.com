"use client";
import React from "react";
import Link from "next/link";
import { Skeleton } from "@/components/ui/skeleton";
import { Insight } from "@/lib/types";
import { cn } from "@/lib/utils";
import {
  ArrowRight, AlertCircle, TrendingUp, Zap,
  ChevronRight,
} from "lucide-react";

/* ── Per-category config ──────────────────────────────────────────────── */
const CATEGORY_CONFIG: Record<string, { icon: React.ElementType; color: string; bg: string }> = {
  ai:            { icon: Zap,         color: "#8b5cf6", bg: "rgba(139,92,246,0.10)" },
  seo:           { icon: TrendingUp,  color: "#6366f1", bg: "rgba(99,102,241,0.10)" },
  ads:           { icon: AlertCircle, color: "#f97316", bg: "rgba(249,115,22,0.10)" },
  gsc:           { icon: TrendingUp,  color: "#3b82f6", bg: "rgba(59,130,246,0.10)" },
  "cross-channel": { icon: AlertCircle, color: "#ec4899", bg: "rgba(236,72,153,0.10)" },
};

/* ── Priority config ──────────────────────────────────────────────────── */
const PRIORITY_CONFIG: Record<string, { color: string; bg: string; border: string; label: string }> = {
  P1: {
    color: "#ef4444",
    bg: "rgba(239,68,68,0.06)",
    border: "rgba(239,68,68,0.20)",
    label: "Critical",
  },
  P2: {
    color: "#eab308",
    bg: "rgba(234,179,8,0.06)",
    border: "rgba(234,179,8,0.20)",
    label: "Important",
  },
  P3: {
    color: "#22c55e",
    bg: "rgba(34,197,94,0.06)",
    border: "rgba(34,197,94,0.15)",
    label: "Nice-to-have",
  },
};

interface TopInsightsProps { insights?: Insight[]; loading?: boolean }

export function TopInsights({ insights, loading }: TopInsightsProps) {
  if (loading) {
    return (
      <div
        className="rounded-xl"
        style={{ background: '#141416', border: '1px solid rgba(255,255,255,0.07)' }}
      >
        <div className="p-5 pb-4">
          <Skeleton className="h-5 w-32" />
        </div>
        <div className="p-5 pt-0 grid md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => <Skeleton key={i} className="h-40" />)}
        </div>
      </div>
    );
  }

  const topInsights = (insights ?? []).slice(0, 3);

  return (
    <div
      className="rounded-xl"
      style={{ background: '#141416', border: '1px solid rgba(255,255,255,0.07)', boxShadow: '0 1px 3px rgba(0,0,0,0.3)' }}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between px-5 py-4"
        style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}
      >
        <div>
          <h3 className="text-[13px] font-semibold text-text-1">Top Insights</h3>
          <p className="text-[11px] text-text-3 mt-0.5">AI-powered recommendations for your brand</p>
        </div>
        <Link
          href="/insights"
          className="flex items-center gap-1 text-[12px] font-medium transition-colors"
          style={{ color: '#818cf8' }}
        >
          View all <ChevronRight size={13} />
        </Link>
      </div>

      {/* Insight cards */}
      <div className="p-4 grid md:grid-cols-3 gap-3">
        {topInsights.map((insight, idx) => {
          const catConf  = CATEGORY_CONFIG[insight.category]  ?? CATEGORY_CONFIG.seo;
          const priConf  = PRIORITY_CONFIG[insight.priority]  ?? PRIORITY_CONFIG.P3;
          const Icon     = catConf.icon;

          return (
            <div
              key={insight.id}
              className="relative rounded-xl p-4 flex flex-col group overflow-hidden transition-all hover:-translate-y-px"
              style={{
                background: priConf.bg,
                border: `1px solid ${priConf.border}`,
                boxShadow: `0 1px 3px rgba(0,0,0,0.2)`,
              }}
            >
              {/* Left accent bar */}
              <div
                className="absolute left-0 top-3 bottom-3 w-0.5 rounded-r-full"
                style={{ background: priConf.color }}
              />

              {/* Top row */}
              <div className="flex items-start gap-2 mb-3">
                <div
                  className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0"
                  style={{ background: catConf.bg }}
                >
                  <Icon size={13} style={{ color: catConf.color }} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    {/* Priority badge */}
                    <span
                      className="text-[9px] font-bold uppercase tracking-wide px-1.5 py-0.5 rounded-md"
                      style={{
                        background: `${priConf.color}18`,
                        color: priConf.color,
                        border: `1px solid ${priConf.color}30`,
                      }}
                    >
                      {insight.priority} · {priConf.label}
                    </span>
                    {/* Category badge */}
                    <span
                      className="text-[9px] font-medium capitalize px-1.5 py-0.5 rounded-md"
                      style={{
                        background: catConf.bg,
                        color: catConf.color,
                      }}
                    >
                      {insight.category}
                    </span>
                  </div>
                </div>
              </div>

              {/* Content */}
              <h4 className="text-[13px] font-semibold text-text-1 leading-snug mb-1.5">
                {insight.title}
              </h4>
              <p className="text-[11px] text-text-2 line-clamp-2 leading-relaxed flex-1">
                {insight.description}
              </p>

              {/* Data snippet */}
              {insight.data_snippet && (
                <div
                  className="mt-2 rounded-lg px-2.5 py-1.5 font-mono text-[10px] text-text-2"
                  style={{ background: 'rgba(0,0,0,0.25)', border: '1px solid rgba(255,255,255,0.05)' }}
                >
                  {insight.data_snippet}
                </div>
              )}

              {/* CTA */}
              {insight.action_url && (
                <Link
                  href={insight.action_url}
                  className="mt-3 flex items-center gap-1 text-[11px] font-semibold transition-colors self-start"
                  style={{ color: catConf.color }}
                >
                  {insight.action_label ?? "View Details"}
                  <ArrowRight size={11} />
                </Link>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
