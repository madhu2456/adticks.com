"use client";
import React, { useState } from "react";
import { CheckSquare, Square, Download, CheckCircle } from "lucide-react";
import { Recommendation } from "@/lib/types";

interface RecommendationPanelProps {
  recommendations: Recommendation[];
}

const PRIORITY_COLORS: Record<string, string> = {
  P1: "bg-[#ef4444]/10 text-[#ef4444] border-[#ef4444]/20",
  P2: "bg-[#f97316]/10 text-[#f97316] border-[#f97316]/20",
  P3: "bg-[#f59e0b]/10 text-[#f59e0b] border-[#f59e0b]/20",
};

const CATEGORY_LABELS: Record<string, string> = {
  seo: "SEO",
  ai: "AI",
  gsc: "GSC",
  ads: "Ads",
  "cross-channel": "Cross",
};

export function RecommendationPanel({ recommendations }: RecommendationPanelProps) {
  const [completed, setCompleted] = useState<Set<string>>(new Set());

  function toggle(id: string) {
    setCompleted((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function handleExport() {
    const lines = recommendations.map((r, i) => {
      const done = completed.has(r.id) ? "[x]" : "[ ]";
      return `${i + 1}. ${done} [${r.priority}] ${r.title}\n   ${r.description}`;
    });
    const text = `AdTicks Action Plan\n${"=".repeat(40)}\n\n${lines.join("\n\n")}`;
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "adticks-action-plan.txt";
    a.click();
    URL.revokeObjectURL(url);
  }

  const doneCount = completed.size;
  const total = recommendations.length;

  return (
    <div className="bg-[#1e293b] rounded-xl border border-[#334155] overflow-hidden sticky top-6">
      {/* Header */}
      <div className="flex items-center gap-2 px-5 py-4 border-b border-[#334155]">
        <div className="w-7 h-7 rounded-lg bg-[#10b981]/10 flex items-center justify-center">
          <CheckCircle className="h-4 w-4 text-[#10b981]" />
        </div>
        <h3 className="text-[#f1f5f9] font-semibold text-sm">Action Plan</h3>
      </div>

      {/* Progress */}
      <div className="px-5 py-3 border-b border-[#334155] bg-[#0f172a]/30">
        <div className="flex items-center justify-between text-xs text-[#94a3b8] mb-2">
          <span>{doneCount} of {total} completed</span>
          <span>{Math.round((doneCount / total) * 100)}%</span>
        </div>
        <div className="h-1.5 bg-[#334155] rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-[#10b981] to-[#6366f1] rounded-full transition-all duration-300"
            style={{ width: `${(doneCount / total) * 100}%` }}
          />
        </div>
      </div>

      {/* Recommendations */}
      <div className="p-4 space-y-2 max-h-[500px] overflow-y-auto">
        {recommendations.map((rec, idx) => {
          const done = completed.has(rec.id);
          return (
            <button
              key={rec.id}
              onClick={() => toggle(rec.id)}
              className={`w-full text-left flex items-start gap-3 p-3 rounded-lg transition-all ${
                done ? "opacity-50 bg-[#334155]/20" : "hover:bg-[#334155]/30 bg-[#0f172a]/20"
              }`}
            >
              <div className="shrink-0 mt-0.5 text-[#94a3b8]">
                {done ? (
                  <CheckSquare className="h-4 w-4 text-[#10b981]" />
                ) : (
                  <Square className="h-4 w-4" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5 mb-1">
                  <span className="text-xs font-bold text-[#94a3b8]">{idx + 1}.</span>
                  <span
                    className={`text-[10px] font-semibold px-1.5 py-0.5 rounded border ${PRIORITY_COLORS[rec.priority] ?? ""}`}
                  >
                    {rec.priority}
                  </span>
                  <span className="text-[10px] text-[#475569] bg-[#334155] px-1.5 py-0.5 rounded">
                    {CATEGORY_LABELS[rec.category]}
                  </span>
                </div>
                <p className={`text-xs font-medium leading-snug ${done ? "line-through text-[#475569]" : "text-[#f1f5f9]"}`}>
                  {rec.title}
                </p>
                {!done && (
                  <p className="text-[11px] text-[#94a3b8] mt-0.5 leading-relaxed line-clamp-2">
                    {rec.description}
                  </p>
                )}
              </div>
            </button>
          );
        })}
      </div>

      {/* Export */}
      <div className="px-4 py-3 border-t border-[#334155]">
        <button
          onClick={handleExport}
          className="w-full flex items-center justify-center gap-2 bg-[#334155] hover:bg-[#475569] text-[#f1f5f9] rounded-lg py-2 text-xs font-medium transition-colors"
        >
          <Download className="h-3.5 w-3.5" />
          Export Action Plan
        </button>
      </div>
    </div>
  );
}
