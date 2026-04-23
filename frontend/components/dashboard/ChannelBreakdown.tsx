"use client";
import React, { useState } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { BarChart } from "@/components/charts/BarChart";
import { ChannelPerformance } from "@/lib/types";
import { cn } from "@/lib/utils";
import { BarChart2, TrendingUp } from "lucide-react";

interface ChannelBreakdownProps {
  data?: ChannelPerformance[];
  loading?: boolean;
}

const PERIOD_OPTIONS = ["7d", "14d", "30d"] as const;
type Period = typeof PERIOD_OPTIONS[number];

export function ChannelBreakdown({ data, loading }: ChannelBreakdownProps) {
  const [period, setPeriod] = useState<Period>("7d");

  if (loading) {
    return (
      <div
        className="rounded-xl"
        style={{ background: 'var(--surface-2)', border: '1px solid var(--border)' }}
      >
        <div className="p-5 pb-4"><Skeleton className="h-5 w-44" /></div>
        <div className="px-5 pb-5"><Skeleton className="h-56 w-full" /></div>
      </div>
    );
  }

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
        className="flex items-center justify-between px-5 py-4"
        style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}
      >
        <div className="flex items-center gap-2.5">
          <div
            className="w-7 h-7 rounded-lg flex items-center justify-center"
            style={{ background: 'rgba(99,102,241,0.12)', border: '1px solid rgba(99,102,241,0.2)' }}
          >
            <BarChart2 size={13} className="text-primary" />
          </div>
          <div>
            <h3 className="text-[13px] font-semibold text-text-1">Channel Performance</h3>
            <p className="text-[11px] text-text-3 mt-0.5">This week vs. last week</p>
          </div>
        </div>

        {/* Period pills */}
        <div
          className="flex items-center gap-0.5 p-0.5 rounded-lg"
          style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)' }}
        >
          {PERIOD_OPTIONS.map((opt) => (
            <button
              key={opt}
              onClick={() => setPeriod(opt)}
              className={cn(
                "h-6 px-2.5 rounded-md text-[11px] font-medium transition-all",
                period === opt
                  ? "text-text-1 shadow-sm"
                  : "text-text-3 hover:text-text-2",
              )}
              style={
                period === opt
                  ? { background: 'rgba(255,255,255,0.08)' }
                  : {}
              }
            >
              {opt}
            </button>
          ))}
        </div>
      </div>

      {/* Chart */}
      <div className="flex-1 p-5 pt-4">
        <BarChart
          data={data ?? []}
          xKey="channel"
          height={220}
          bars={[
            { key: "this_week", name: "This Week", color: "#6366f1" },
            { key: "last_week", name: "Last Week", color: "rgba(255,255,255,0.08)" },
          ]}
        />
      </div>

      {/* Legend */}
      <div
        className="flex items-center gap-4 px-5 py-2.5"
        style={{ borderTop: '1px solid rgba(255,255,255,0.05)', background: 'rgba(0,0,0,0.15)' }}
      >
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-1.5 rounded-full" style={{ background: '#6366f1' }} />
          <span className="text-[10px] text-text-3">This week</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-1.5 rounded-full" style={{ background: 'rgba(255,255,255,0.15)' }} />
          <span className="text-[10px] text-text-3">Last week</span>
        </div>
        <div className="ml-auto flex items-center gap-1 text-[10px] text-success">
          <TrendingUp size={10} />
          +8.3% overall
        </div>
      </div>
    </div>
  );
}
