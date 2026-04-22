"use client";
import React from "react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { cn } from "@/lib/utils";

interface RadialChartProps {
  data: { name: string; value: number; color: string }[];
  innerRadius?: number;
  outerRadius?: number;
  height?: number;
  className?: string;
  showLegend?: boolean;
  centerLabel?: string;
  centerValue?: string | number;
}

export function RadialChart({
  data, innerRadius = 60, outerRadius = 90, height = 260, className,
  showLegend = true, centerLabel, centerValue,
}: RadialChartProps) {
  return (
    <div className={cn("w-full", className)} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={innerRadius}
            outerRadius={outerRadius}
            paddingAngle={3}
            dataKey="value"
            startAngle={90}
            endAngle={-270}
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} strokeWidth={0} />
            ))}
          </Pie>
          {centerValue !== undefined && (
            <text x="50%" y="50%" textAnchor="middle" dominantBaseline="middle">
              <tspan x="50%" dy="-8" fontSize="28" fontWeight="700" fill="#f1f5f9">
                {centerValue}
              </tspan>
              {centerLabel && (
                <tspan x="50%" dy="24" fontSize="11" fill="#94a3b8">
                  {centerLabel}
                </tspan>
              )}
            </text>
          )}
          <Tooltip
            formatter={(value: number, name: string) => [`${value}%`, name]}
            contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: "8px", fontSize: "12px", color: "#f1f5f9" }}
          />
          {showLegend && (
            <Legend
              iconType="circle"
              iconSize={8}
              wrapperStyle={{ fontSize: "12px", color: "#94a3b8" }}
            />
          )}
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
