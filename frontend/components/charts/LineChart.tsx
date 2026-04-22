"use client";
import React from "react";
import {
  LineChart as RechartsLine,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { cn } from "@/lib/utils";

interface LineChartProps {
  data: Record<string, unknown>[];
  lines: { key: string; color: string; name?: string }[];
  xKey?: string;
  height?: number;
  className?: string;
  formatY?: (value: number) => string;
  formatTooltip?: (value: number, name: string) => string;
}

const CustomTooltip = ({ active, payload, label, formatTooltip }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-surface border border-border rounded-lg p-3 shadow-xl text-xs">
      <p className="text-text-muted mb-2 font-medium">{label}</p>
      {payload.map((p: any) => (
        <div key={p.dataKey} className="flex items-center gap-2 mb-1">
          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: p.color }} />
          <span className="text-text-muted">{p.name}:</span>
          <span className="font-semibold text-text-primary">
            {formatTooltip ? formatTooltip(p.value, p.name) : p.value}
          </span>
        </div>
      ))}
    </div>
  );
};

export function LineChart({ data, lines, xKey = "date", height = 300, className, formatY, formatTooltip }: LineChartProps) {
  return (
    <div className={cn("w-full", className)} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <RechartsLine data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey={xKey} tick={{ fill: "#94a3b8", fontSize: 11 }} tickLine={false} axisLine={false} />
          <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} tickLine={false} axisLine={false} tickFormatter={formatY} width={40} />
          <Tooltip content={<CustomTooltip formatTooltip={formatTooltip} />} />
          {lines.length > 1 && <Legend wrapperStyle={{ fontSize: "12px", color: "#94a3b8" }} />}
          {lines.map((l) => (
            <Line
              key={l.key}
              type="monotone"
              dataKey={l.key}
              name={l.name ?? l.key}
              stroke={l.color}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: l.color }}
            />
          ))}
        </RechartsLine>
      </ResponsiveContainer>
    </div>
  );
}
