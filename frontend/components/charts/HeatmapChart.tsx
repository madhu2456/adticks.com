"use client";
import React from "react";
import { cn } from "@/lib/utils";

interface HeatmapDataPoint {
  x: string;
  y: string;
  value: number;
}

interface HeatmapChartProps {
  data: HeatmapDataPoint[];
  xLabels: string[];
  yLabels: string[];
  className?: string;
  colorRange?: [string, string];
}

export function HeatmapChart({ data, xLabels, yLabels, className }: HeatmapChartProps) {
  const maxValue = Math.max(...data.map((d) => d.value), 1);

  const getValue = (x: string, y: string) =>
    data.find((d) => d.x === x && d.y === y)?.value ?? 0;

  const getColor = (value: number) => {
    const intensity = value / maxValue;
    if (intensity === 0) return "bg-surface2";
    if (intensity < 0.25) return "bg-indigo-900/60";
    if (intensity < 0.5) return "bg-indigo-700/70";
    if (intensity < 0.75) return "bg-indigo-500/80";
    return "bg-indigo-400";
  };

  return (
    <div className={cn("overflow-auto", className)}>
      <div className="inline-block min-w-full">
        {/* X labels */}
        <div className="flex gap-1 mb-1 ml-20">
          {xLabels.map((label) => (
            <div key={label} className="w-10 text-center text-xs text-text-muted truncate">{label}</div>
          ))}
        </div>
        {/* Rows */}
        {yLabels.map((y) => (
          <div key={y} className="flex items-center gap-1 mb-1">
            <div className="w-20 text-right text-xs text-text-muted pr-2 truncate">{y}</div>
            {xLabels.map((x) => {
              const val = getValue(x, y);
              return (
                <div
                  key={x}
                  className={cn("w-10 h-8 rounded flex items-center justify-center text-xs font-medium transition-colors cursor-default", getColor(val))}
                  title={`${y} / ${x}: ${val}`}
                >
                  {val > 0 ? val : ""}
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}
