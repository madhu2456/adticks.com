"use client";
import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { RadialChart } from "@/components/charts/RadialChart";
import { SOVData } from "@/lib/types";

const COLORS = ["#6366f1", "#ef4444", "#3b82f6", "#10b981", "#f97316"];

interface SOVChartProps {
  data?: SOVData[];
  loading?: boolean;
}

export function SOVChart({ data = [], loading }: SOVChartProps) {
  if (loading) return <Card><CardHeader><Skeleton className="h-5 w-40" /></CardHeader><CardContent><Skeleton className="h-64" /></CardContent></Card>;

  const chartData = data.map((d, i) => ({
    name: d.brand,
    value: d.percentage,
    color: d.is_self ? "#6366f1" : COLORS[i + 1] ?? "#94a3b8",
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Share of Voice</CardTitle>
        <p className="text-xs text-text-muted">Brand mentions across AI responses</p>
      </CardHeader>
      <CardContent>
        <RadialChart data={chartData} height={240} innerRadius={55} outerRadius={85} centerLabel="mentions" />
        <div className="mt-4 space-y-2">
          {data.map((d, i) => (
            <div key={d.brand} className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: d.is_self ? "#6366f1" : COLORS[i + 1] ?? "#94a3b8" }} />
                <span className={d.is_self ? "text-primary font-semibold" : "text-text-muted"}>{d.brand}</span>
                {d.is_self && <span className="text-xs bg-primary/20 text-primary px-1.5 py-0.5 rounded">You</span>}
              </div>
              <div className="flex items-center gap-3">
                <span className="text-text-muted text-xs">{d.mention_count} mentions</span>
                <span className="font-semibold text-text-primary w-10 text-right">{d.percentage}%</span>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
