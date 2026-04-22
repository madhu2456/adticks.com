"use client";
import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface DataPoint {
  date: string;
  clicks: number;
  impressions: number;
}

interface ImpressionsChartProps {
  data: DataPoint[];
}

function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ name: string; value: number; color: string }>; label?: string }) {
  if (!active || !payload || !payload.length) return null;
  return (
    <div className="bg-[#1e293b] border border-[#334155] rounded-lg px-4 py-3 shadow-xl text-sm">
      <p className="text-[#94a3b8] mb-2 text-xs">{label}</p>
      {payload.map((entry) => (
        <div key={entry.name} className="flex items-center gap-2 mb-1">
          <div className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
          <span className="text-[#94a3b8] capitalize">{entry.name}:</span>
          <span className="text-[#f1f5f9] font-medium">{entry.value.toLocaleString()}</span>
        </div>
      ))}
    </div>
  );
}

export function ImpressionsChart({ data }: ImpressionsChartProps) {
  const formatted = data.map((d) => ({
    ...d,
    date: new Date(d.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
  }));

  return (
    <div className="bg-[#1e293b] rounded-xl border border-[#334155] p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-[#f1f5f9] font-semibold text-sm">Clicks &amp; Impressions</h3>
          <p className="text-xs text-[#94a3b8] mt-0.5">Last 30 days</p>
        </div>
        <div className="flex items-center gap-4 text-xs text-[#94a3b8]">
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-[#6366f1] inline-block rounded" />
            Clicks
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-[#8b5cf6] inline-block rounded" />
            Impressions
          </span>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={formatted} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis
            dataKey="date"
            tick={{ fill: "#94a3b8", fontSize: 11 }}
            tickLine={false}
            axisLine={false}
            interval={4}
          />
          <YAxis
            yAxisId="clicks"
            orientation="left"
            tick={{ fill: "#94a3b8", fontSize: 11 }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v) => v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v}
          />
          <YAxis
            yAxisId="impressions"
            orientation="right"
            tick={{ fill: "#94a3b8", fontSize: 11 }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v) => v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v}
          />
          <Tooltip content={<CustomTooltip />} />
          <Line
            yAxisId="clicks"
            type="monotone"
            dataKey="clicks"
            stroke="#6366f1"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: "#6366f1" }}
          />
          <Line
            yAxisId="impressions"
            type="monotone"
            dataKey="impressions"
            stroke="#8b5cf6"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: "#8b5cf6" }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
