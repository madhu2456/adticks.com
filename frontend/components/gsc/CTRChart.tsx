"use client";
import React from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from "recharts";

interface DataPoint {
  date: string;
  ctr: number;
}

interface CTRChartProps {
  data: DataPoint[];
}

function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ value: number }>; label?: string }) {
  if (!active || !payload || !payload.length) return null;
  return (
    <div className="bg-[#1e293b] border border-[#334155] rounded-lg px-4 py-3 shadow-xl text-sm">
      <p className="text-[#94a3b8] mb-1 text-xs">{label}</p>
      <div className="flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-[#10b981]" />
        <span className="text-[#94a3b8]">CTR:</span>
        <span className="text-[#f1f5f9] font-medium">{payload[0].value.toFixed(2)}%</span>
      </div>
    </div>
  );
}

export function CTRChart({ data }: CTRChartProps) {
  const formatted = data.map((d) => ({
    ...d,
    date: new Date(d.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    ctr: parseFloat(d.ctr.toFixed(2)),
  }));

  const avgCTR = parseFloat(
    (data.reduce((sum, d) => sum + d.ctr, 0) / data.length).toFixed(2)
  );

  return (
    <div className="bg-[#1e293b] rounded-xl border border-[#334155] p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-[#f1f5f9] font-semibold text-sm">Click-Through Rate</h3>
          <p className="text-xs text-[#94a3b8] mt-0.5">Last 30 days</p>
        </div>
        <div className="flex items-center gap-2 bg-[#10b981]/10 border border-[#10b981]/20 rounded-lg px-3 py-1.5">
          <span className="text-xs text-[#94a3b8]">Avg CTR:</span>
          <span className="text-sm font-semibold text-[#10b981]">{avgCTR}%</span>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={formatted} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="ctrGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis
            dataKey="date"
            tick={{ fill: "#94a3b8", fontSize: 11 }}
            tickLine={false}
            axisLine={false}
            interval={4}
          />
          <YAxis
            tick={{ fill: "#94a3b8", fontSize: 11 }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v) => `${v}%`}
          />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine
            y={avgCTR}
            stroke="#10b981"
            strokeDasharray="6 3"
            strokeOpacity={0.6}
            label={{ value: `Avg ${avgCTR}%`, fill: "#10b981", fontSize: 10, position: "insideTopRight" }}
          />
          <Area
            type="monotone"
            dataKey="ctr"
            stroke="#10b981"
            strokeWidth={2}
            fill="url(#ctrGradient)"
            dot={false}
            activeDot={{ r: 4, fill: "#10b981" }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
