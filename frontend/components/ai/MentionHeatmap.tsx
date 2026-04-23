"use client";
import React, { useState } from "react";

interface HeatmapData {
  category: string;
  brands: { name: string; count: number; percentage: number; isSelf?: boolean }[];
}

const DEFAULT_DATA: HeatmapData[] = [
  {
    category: "Brand Awareness",
    brands: [
      { name: "You", count: 0, percentage: 0, isSelf: true },
      { name: "Comp A", count: 0, percentage: 0 },
      { name: "Comp B", count: 0, percentage: 0 },
      { name: "Comp C", count: 0, percentage: 0 },
    ],
  },
];

function cellColor(pct: number, isSelf?: boolean): string {
  if (pct === 0) return "bg-[#0f172a]";
  if (isSelf) {
    if (pct >= 70) return "bg-[#6366f1]";
    if (pct >= 40) return "bg-[#6366f1]/60";
    if (pct >= 20) return "bg-[#6366f1]/30";
    return "bg-[#6366f1]/15";
  } else {
    if (pct >= 80) return "bg-[#8b5cf6]";
    if (pct >= 60) return "bg-[#8b5cf6]/70";
    if (pct >= 40) return "bg-[#8b5cf6]/45";
    if (pct >= 20) return "bg-[#8b5cf6]/25";
    return "bg-[#8b5cf6]/12";
  }
}

interface TooltipState {
  visible: boolean;
  x: number;
  y: number;
  category: string;
  brand: string;
  count: number;
  percentage: number;
}

export function MentionHeatmap() {
  const [tooltip, setTooltip] = useState<TooltipState>({
    visible: false, x: 0, y: 0, category: "", brand: "", count: 0, percentage: 0,
  });

  const brands = DEFAULT_DATA[0].brands;

  function handleMouseEnter(
    e: React.MouseEvent,
    category: string,
    brand: { name: string; count: number; percentage: number }
  ) {
    const rect = (e.target as HTMLElement).getBoundingClientRect();
    setTooltip({
      visible: true,
      x: rect.left + rect.width / 2,
      y: rect.top - 8,
      category,
      brand: brand.name,
      count: brand.count,
      percentage: brand.percentage,
    });
  }

  return (
    <div className="bg-[#1e293b] rounded-xl border border-[#334155] p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-[#f1f5f9] font-semibold text-sm">Mention Frequency Heatmap</h3>
          <p className="text-xs text-[#94a3b8] mt-0.5">Prompt categories vs. brand mentions</p>
        </div>
        <div className="flex items-center gap-3 text-xs text-[#94a3b8]">
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-sm bg-[#6366f1] inline-block" />
            Your Brand
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-sm bg-[#8b5cf6] inline-block" />
            Competitors
          </span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full" style={{ minWidth: 520 }}>
          <thead>
            <tr>
              <th className="text-left text-xs font-medium text-[#94a3b8] pb-3 pr-4 w-40">
                Category
              </th>
              {brands.map((b) => (
                <th key={b.name} className="text-center text-xs font-medium pb-3 px-2">
                  <span className={b.isSelf ? "text-[#6366f1] font-semibold" : "text-[#94a3b8]"}>
                    {b.name}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="space-y-2">
            {DEFAULT_DATA.map((row) => (
              <tr key={row.category}>
                <td className="text-xs font-medium text-[#94a3b8] pr-4 py-1.5 whitespace-nowrap">
                  {row.category}
                </td>
                {row.brands.map((brand) => (
                  <td key={brand.name} className="px-2 py-1.5 text-center">
                    <div
                      className={`mx-auto w-14 h-10 rounded-lg flex flex-col items-center justify-center cursor-default transition-transform hover:scale-105 ${cellColor(brand.percentage, brand.isSelf)}`}
                      onMouseEnter={(e) => handleMouseEnter(e, row.category, brand)}
                      onMouseLeave={() => setTooltip((t) => ({ ...t, visible: false }))}
                    >
                      <span className="text-[10px] font-bold text-white">{brand.count}</span>
                      <span className="text-[9px] text-white/70">{brand.percentage}%</span>
                    </div>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Scale legend */}
      <div className="mt-5 flex items-center gap-2">
        <span className="text-xs text-[#475569]">Low</span>
        <div className="flex gap-0.5">
          {[15, 25, 45, 70, 100].map((opacity) => (
            <div
              key={opacity}
              className="w-5 h-3 rounded-sm"
              style={{ backgroundColor: `rgba(99,102,241,${opacity / 100})` }}
            />
          ))}
        </div>
        <span className="text-xs text-[#475569]">High</span>
      </div>

      {/* Tooltip */}
      {tooltip.visible && (
        <div
          className="fixed z-50 pointer-events-none"
          style={{ left: tooltip.x, top: tooltip.y, transform: "translate(-50%, -100%)" }}
        >
          <div className="bg-[#0f172a] border border-[#334155] rounded-lg px-3 py-2.5 shadow-xl text-xs whitespace-nowrap mb-1">
            <p className="font-semibold text-[#f1f5f9] mb-1">
              {tooltip.brand} · {tooltip.category}
            </p>
            <div className="flex items-center gap-3">
              <span className="text-[#94a3b8]">Mentions: <span className="text-[#f1f5f9] font-medium">{tooltip.count}</span></span>
              <span className="text-[#94a3b8]">Coverage: <span className="text-[#6366f1] font-medium">{tooltip.percentage}%</span></span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
