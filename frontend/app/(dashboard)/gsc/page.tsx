"use client";
import React, { useState } from "react";
import {
  BarChart2, RefreshCw, Link2, MousePointerClick,
  Eye, Percent, Hash, TrendingUp,
} from "lucide-react";
import { ImpressionsChart } from "@/components/gsc/ImpressionsChart";
import { CTRChart } from "@/components/gsc/CTRChart";
import { QueryTable } from "@/components/gsc/QueryTable";
import { mockGSCQueries, mockGSCPages, mockGSCMetrics } from "@/lib/mockData";

function StatCard({ icon: Icon, label, value, sub }: { icon: React.ElementType; label: string; value: string; sub?: string }) {
  return (
    <div className="bg-[#1e293b] rounded-xl border border-[#334155] p-5">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-8 h-8 rounded-lg bg-[#6366f1]/10 flex items-center justify-center">
          <Icon className="h-4 w-4 text-[#6366f1]" />
        </div>
        <span className="text-xs text-[#94a3b8] font-medium">{label}</span>
      </div>
      <p className="text-2xl font-bold text-[#f1f5f9]">{value}</p>
      {sub && <p className="text-xs text-[#94a3b8] mt-1">{sub}</p>}
    </div>
  );
}

export default function GSCPage() {
  const [isConnected, setIsConnected] = useState(false);
  const [activeTab, setActiveTab] = useState<"queries" | "pages">("queries");
  const [syncing, setSyncing] = useState(false);

  const totalClicks = mockGSCQueries.reduce((s, q) => s + q.clicks, 0);
  const totalImpressions = mockGSCMetrics.reduce((s, m) => s + m.impressions, 0);
  const avgCTR = (mockGSCMetrics.reduce((s, m) => s + m.ctr, 0) / mockGSCMetrics.length).toFixed(2);
  const avgPosition = (mockGSCMetrics.reduce((s, m) => s + m.position, 0) / mockGSCMetrics.length).toFixed(1);

  function handleSync() {
    setSyncing(true);
    setTimeout(() => setSyncing(false), 2000);
  }

  if (!isConnected) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center p-6">
        <div className="max-w-lg w-full">
          <div className="bg-[#1e293b] rounded-2xl border border-[#334155] p-8 text-center">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#6366f1]/20 to-[#8b5cf6]/20 border border-[#6366f1]/30 flex items-center justify-center mx-auto mb-6">
              <BarChart2 className="h-8 w-8 text-[#6366f1]" />
            </div>
            <h2 className="text-xl font-bold text-[#f1f5f9] mb-2">Connect Google Search Console</h2>
            <p className="text-[#94a3b8] text-sm mb-6 leading-relaxed">
              Sync your GSC data to track clicks, impressions, CTR, and rankings directly inside AdTicks — updated daily.
            </p>

            <div className="grid grid-cols-2 gap-3 mb-8 text-left">
              {[
                { icon: MousePointerClick, label: "Clicks & Impressions", desc: "Track daily click data" },
                { icon: Percent, label: "CTR Analysis", desc: "Monitor click-through rates" },
                { icon: Hash, label: "Position Tracking", desc: "Average ranking positions" },
                { icon: TrendingUp, label: "Query Intelligence", desc: "Top queries and pages" },
              ].map(({ icon: Ic, label, desc }) => (
                <div key={label} className="flex items-start gap-3 bg-[#0f172a]/50 rounded-lg p-3">
                  <div className="w-7 h-7 rounded-md bg-[#6366f1]/10 flex items-center justify-center shrink-0 mt-0.5">
                    <Ic className="h-3.5 w-3.5 text-[#6366f1]" />
                  </div>
                  <div>
                    <p className="text-xs font-medium text-[#f1f5f9]">{label}</p>
                    <p className="text-xs text-[#94a3b8]">{desc}</p>
                  </div>
                </div>
              ))}
            </div>

            <button
              onClick={() => alert("Redirecting to Google OAuth...")}
              className="w-full flex items-center justify-center gap-2 bg-[#6366f1] hover:bg-[#4f46e5] text-white font-semibold rounded-xl py-3 text-sm transition-colors shadow-lg shadow-[#6366f1]/25 mb-3"
            >
              <Link2 className="h-4 w-4" />
              Connect GSC
            </button>
            <button
              onClick={() => setIsConnected(true)}
              className="w-full text-sm text-[#94a3b8] hover:text-[#f1f5f9] py-2 transition-colors"
            >
              Use Demo Data instead
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#f1f5f9]">Google Search Console</h1>
          <p className="text-sm text-[#94a3b8] mt-1">Last synced: 2 hours ago</p>
        </div>
        <button
          onClick={handleSync}
          disabled={syncing}
          className="flex items-center gap-2 bg-[#6366f1]/10 hover:bg-[#6366f1]/20 border border-[#6366f1]/30 text-[#6366f1] rounded-xl px-4 py-2 text-sm font-medium transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${syncing ? "animate-spin" : ""}`} />
          {syncing ? "Syncing..." : "Sync Now"}
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={MousePointerClick} label="Total Clicks" value={totalClicks.toLocaleString()} sub="Last 28 days" />
        <StatCard icon={Eye} label="Total Impressions" value={totalImpressions.toLocaleString()} sub="Last 28 days" />
        <StatCard icon={Percent} label="Avg CTR" value={`${avgCTR}%`} sub="Click-through rate" />
        <StatCard icon={Hash} label="Avg Position" value={`#${avgPosition}`} sub="Search ranking" />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2">
          <ImpressionsChart data={mockGSCMetrics} />
        </div>
        <div>
          <CTRChart data={mockGSCMetrics} />
        </div>
      </div>

      {/* Tabs */}
      <div>
        <div className="flex gap-1 bg-[#0f172a] rounded-xl p-1 mb-4 w-fit border border-[#334155]">
          {(["queries", "pages"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition-colors ${
                activeTab === tab
                  ? "bg-[#6366f1] text-white shadow"
                  : "text-[#94a3b8] hover:text-[#f1f5f9]"
              }`}
            >
              Top {tab === "queries" ? "Queries" : "Pages"}
            </button>
          ))}
        </div>
        <QueryTable
          data={activeTab === "queries" ? mockGSCQueries : mockGSCPages}
          title={activeTab === "queries" ? "Top Queries" : "Top Pages"}
        />
      </div>
    </div>
  );
}
