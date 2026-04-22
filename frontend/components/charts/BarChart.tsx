"use client";
import React from "react";
import {
  BarChart as RechartsBar,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Cell,
} from "recharts";
import { cn } from "@/lib/utils";

interface BarChartProps {
  data: object[];
  bars: { key: string; color: string; name?: string }[];
  xKey?: string;
  height?: number;
  className?: string;
  horizontal?: boolean;
  formatY?: (v: number) => string;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-surface border border-border rounded-lg p-3 shadow-xl text-xs">
      <p className="text-text-muted mb-2 font-medium">{label}</p>
      {payload.map((p: any) => (
        <div key={p.dataKey} className="flex items-center gap-2 mb-1">
          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: p.fill }} />
          <span className="text-text-muted">{p.name}:</span>
          <span className="font-semibold text-text-primary">{p.value}</span>
        </div>
      ))}
    </div>
  );
};

export function BarChart({ data, bars, xKey = "name", height = 300, className, horizontal, formatY }: BarChartProps) {
  return (
    <div className={cn("w-full", className)} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <RechartsBar
          data={data}
          layout={horizontal ? "vertical" : "horizontal"}
          margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          {horizontal ? (
            <>
              <XAxis type="number" tick={{ fill: "#94a3b8", fontSize: 11 }} tickLine={false} axisLine={false} tickFormatter={formatY} />
              <YAxis type="category" dataKey={xKey} tick={{ fill: "#94a3b8", fontSize: 11 }} tickLine={false} axisLine={false} width={100} />
            </>
          ) : (
            <>
              <XAxis dataKey={xKey} tick={{ fill: "#94a3b8", fontSize: 11 }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} tickLine={false} axisLine={false} tickFormatter={formatY} width={40} />
            </>
          )}
          <Tooltip content={<CustomTooltip />} />
          {bars.length > 1 && <Legend wrapperStyle={{ fontSize: "12px", color: "#94a3b8" }} />}
          {bars.map((b) => (
            <Bar key={b.key} dataKey={b.key} name={b.name ?? b.key} fill={b.color} radius={[4, 4, 0, 0]} maxBarSize={40} />
          ))}
        </RechartsBar>
      </ResponsiveContainer>
    </div>
  );
}
