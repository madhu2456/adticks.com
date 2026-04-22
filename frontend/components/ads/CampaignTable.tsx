"use client";
import React from "react";
import { AdCampaign } from "@/lib/types";

interface CampaignTableProps {
  campaigns: AdCampaign[];
}

function StatusBadge({ status }: { status: AdCampaign["status"] }) {
  const map: Record<string, string> = {
    active: "bg-[#10b981]/10 text-[#10b981] border-[#10b981]/20",
    paused: "bg-[#334155] text-[#94a3b8] border-[#475569]/30",
    ended: "bg-[#ef4444]/10 text-[#ef4444] border-[#ef4444]/20",
  };
  const labels: Record<string, string> = { active: "Active", paused: "Paused", ended: "Ended" };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border ${map[status]}`}>
      <span className={`w-1.5 h-1.5 rounded-full mr-1.5 ${status === "active" ? "bg-[#10b981]" : status === "paused" ? "bg-[#94a3b8]" : "bg-[#ef4444]"}`} />
      {labels[status]}
    </span>
  );
}

function ROASBadge({ roas }: { roas: number }) {
  const color =
    roas >= 3 ? "text-[#10b981]" :
    roas >= 1 ? "text-[#f59e0b]" :
    "text-[#ef4444]";
  return <span className={`font-semibold text-sm ${color}`}>{roas.toFixed(1)}x</span>;
}

export function CampaignTable({ campaigns }: CampaignTableProps) {
  return (
    <div className="bg-[#1e293b] rounded-xl border border-[#334155] overflow-hidden">
      <div className="px-5 py-4 border-b border-[#334155]">
        <h3 className="text-[#f1f5f9] font-semibold text-sm">Campaigns</h3>
        <p className="text-xs text-[#94a3b8] mt-0.5">{campaigns.length} campaigns</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm min-w-[900px]">
          <thead>
            <tr className="bg-[#0f172a]/40">
              {["Campaign", "Status", "Clicks", "Impressions", "CTR", "CPC", "Conversions", "ROAS", "Spend"].map((h) => (
                <th key={h} className="px-4 py-3 text-xs font-medium text-[#94a3b8] uppercase tracking-wide text-left whitespace-nowrap">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {campaigns.map((c) => (
              <tr key={c.id} className="border-t border-[#334155]/50 hover:bg-[#334155]/20 transition-colors">
                <td className="px-4 py-3.5 text-[#f1f5f9] font-medium whitespace-nowrap">{c.name}</td>
                <td className="px-4 py-3.5"><StatusBadge status={c.status} /></td>
                <td className="px-4 py-3.5 text-[#f1f5f9]">{c.clicks.toLocaleString()}</td>
                <td className="px-4 py-3.5 text-[#94a3b8]">{c.impressions.toLocaleString()}</td>
                <td className="px-4 py-3.5 text-[#94a3b8]">{c.ctr.toFixed(1)}%</td>
                <td className="px-4 py-3.5 text-[#f1f5f9]">${c.cpc.toFixed(2)}</td>
                <td className="px-4 py-3.5 text-[#f1f5f9]">{c.conversions}</td>
                <td className="px-4 py-3.5"><ROASBadge roas={c.roas} /></td>
                <td className="px-4 py-3.5 text-[#f1f5f9] font-medium">${c.spend.toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
