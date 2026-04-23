"use client";
import React, { useEffect, useState } from "react";
import {
  RadialBarChart, RadialBar, ResponsiveContainer,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { VisibilityScore as VisibilityScoreType } from "@/lib/types";
import { getScoreColor } from "@/lib/utils";
import { TrendingUp, TrendingDown, ArrowRight } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

interface Props { score?: VisibilityScoreType; loading?: boolean }

const CHANNELS = [
  { key: "seo",  label: "SEO Hub",        color: "#6366f1", href: "/seo",           trend: 0 },
  { key: "ai",   label: "AI Visibility",  color: "#8b5cf6", href: "/ai-visibility",  trend: 0 },
  { key: "gsc",  label: "Search Console", color: "#3b82f6", href: "/gsc",            trend: 0 },
  { key: "ads",  label: "Google Ads",     color: "#f97316", href: "/ads",            trend: 0 },
] as const;


export function VisibilityScore({ score, loading }: Props) {
  const [animScore, setAnimScore] = useState(0);

  useEffect(() => {
    if (!score) return;
    const start = performance.now();
    const duration = 1100;
    const tick = (now: number) => {
      const p = Math.min((now - start) / duration, 1);
      const e = 1 - Math.pow(1 - p, 3);
      setAnimScore(Math.round(score.overall * e));
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }, [score]);

  if (loading) {
    return (
      <Card>
        <CardHeader><Skeleton className="h-5 w-40" /></CardHeader>
        <CardContent><Skeleton className="h-56 w-full" /></CardContent>
      </Card>
    );
  }
  if (!score) return null;

  const overallColor = getScoreColor(score.overall);

  const gaugeData = [
    { name: "SEO", value: score.seo,  fill: "#6366f1" },
    { name: "AI",  value: score.ai,   fill: "#8b5cf6" },
    { name: "GSC", value: score.gsc,  fill: "#3b82f6" },
    { name: "Ads", value: score.ads,  fill: "#f97316" },
  ];

  const getScoreLabel = (s: number) => {
    if (s >= 80) return "Excellent";
    if (s >= 60) return "Good";
    if (s >= 40) return "Fair";
    return "Needs Work";
  };

  return (
    <div
      className="rounded-xl h-full relative overflow-hidden"
      style={{
        background: '#141416',
        border: '1px solid rgba(255,255,255,0.07)',
        boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
      }}
    >
      {/* Subtle background glow */}
      <div
        className="absolute top-0 right-0 w-48 h-48 pointer-events-none"
        style={{
          background: `radial-gradient(circle at 80% 20%, ${overallColor}15, transparent 70%)`,
          filter: 'blur(20px)',
        }}
      />

      <div className="p-5 pb-4 flex items-center justify-between" style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <div>
          <h3 className="text-[13px] font-semibold text-text-1">Visibility Score</h3>
          <p className="text-[11px] text-text-3 mt-0.5">Unified brand presence index</p>
        </div>
        <div
          className="text-[11px] font-semibold px-2 py-1 rounded-lg"
          style={{
            background: `${overallColor}18`,
            color: overallColor,
            border: `1px solid ${overallColor}25`,
          }}
        >
          {getScoreLabel(score.overall)}
        </div>
      </div>

      <div className="p-5">
        <div className="flex items-center gap-6">
          {/* Radial gauge */}
          <div className="relative flex-shrink-0" style={{ width: 168, height: 168 }}>
            <ResponsiveContainer width="100%" height="100%">
              <RadialBarChart
                cx="50%"
                cy="50%"
                innerRadius={36}
                outerRadius={80}
                data={[...gaugeData].reverse()}
                startAngle={90}
                endAngle={-270}
              >
                <RadialBar
                  dataKey="value"
                  cornerRadius={8}
                  background={{ fill: 'rgba(255,255,255,0.04)' }}
                />
              </RadialBarChart>
            </ResponsiveContainer>

            {/* Center score */}
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span
                className="text-[38px] font-bold tabular-nums leading-none"
                style={{ color: overallColor }}
              >
                {animScore}
              </span>
              <span className="text-[10px] font-medium text-text-3 mt-1 uppercase tracking-wider">Score</span>
            </div>
          </div>

          {/* Channel breakdown */}
          <div className="flex-1 space-y-3 min-w-0">
            {CHANNELS.map((ch) => {
              const val = score[ch.key];
              const positive = ch.trend >= 0;
              return (
                <Link key={ch.key} href={ch.href} className="block group">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[12px] text-text-2 group-hover:text-text-1 transition-colors">{ch.label}</span>
                    <div className="flex items-center gap-2">
                      <span
                        className={cn(
                          "flex items-center gap-0.5 text-[10px] font-semibold",
                          positive ? "text-success" : "text-danger",
                        )}
                      >
                        {positive ? <TrendingUp size={9} /> : <TrendingDown size={9} />}
                        {Math.abs(ch.trend)}%
                      </span>
                      <span className="text-[13px] font-bold tabular-nums" style={{ color: ch.color }}>
                        {val}
                      </span>
                    </div>
                  </div>
                  <div
                    className="h-1.5 rounded-full overflow-hidden"
                    style={{ background: 'rgba(255,255,255,0.05)' }}
                  >
                    <div
                      className="h-full rounded-full transition-all duration-1000"
                      style={{
                        width: `${val}%`,
                        background: `linear-gradient(90deg, ${ch.color}cc, ${ch.color})`,
                        boxShadow: `0 0 6px ${ch.color}40`,
                      }}
                    />
                  </div>
                </Link>
              );
            })}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div
        className="px-5 py-2.5 flex items-center justify-between"
        style={{ borderTop: '1px solid rgba(255,255,255,0.05)', background: 'rgba(0,0,0,0.15)' }}
      >
        <p className="text-[10px] text-text-3">Refreshes every 24 hours</p>
        <Link
          href="/insights"
          className="flex items-center gap-1 text-[11px] font-medium text-primary hover:text-primary/80 transition-colors"
        >
          View full report <ArrowRight size={11} />
        </Link>
      </div>
    </div>
  );
}
