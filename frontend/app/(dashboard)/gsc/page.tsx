"use client";
import React, { useState } from "react";
import {
  BarChart2, RefreshCw, Link2, MousePointerClick,
  Eye, Percent, Hash, TrendingUp,
} from "lucide-react";
import { ImpressionsChart } from "@/components/gsc/ImpressionsChart";
import { CTRChart } from "@/components/gsc/CTRChart";
import { QueryTable } from "@/components/gsc/QueryTable";
const MOCK_QUERIES_EXTENDED = [
  { query: "visibility intelligence platform", clicks: 342, impressions: 4800, ctr: 7.1, position: 3.2, positionChange: 2 },
  { query: "ai seo tools comparison", clicks: 218, impressions: 6200, ctr: 3.5, position: 7.8, positionChange: -1 },
  { query: "best seo dashboard 2024", clicks: 196, impressions: 5100, ctr: 3.8, position: 6.1, positionChange: 3 },
  { query: "chatgpt seo optimization guide", clicks: 187, impressions: 3900, ctr: 4.8, position: 4.5, positionChange: 1 },
  { query: "rank tracking software free", clicks: 164, impressions: 8700, ctr: 1.9, position: 12.3, positionChange: -2 },
  { query: "seo keyword difficulty tool", clicks: 142, impressions: 4200, ctr: 3.4, position: 8.9, positionChange: 0 },
  { query: "content gap analysis tool", clicks: 128, impressions: 3600, ctr: 3.6, position: 9.2, positionChange: 4 },
  { query: "ai brand mentions monitoring", clicks: 112, impressions: 2100, ctr: 5.3, position: 5.7, positionChange: 2 },
  { query: "competitor seo analysis", clicks: 98, impressions: 5400, ctr: 1.8, position: 14.1, positionChange: -3 },
  { query: "organic traffic tracking", clicks: 87, impressions: 3200, ctr: 2.7, position: 11.5, positionChange: 1 },
  { query: "seo reporting software", clicks: 76, impressions: 4900, ctr: 1.6, position: 16.2, positionChange: 0 },
  { query: "llm seo optimization tips", clicks: 71, impressions: 1800, ctr: 3.9, position: 7.3, positionChange: 5 },
  { query: "saas seo strategy guide", clicks: 65, impressions: 2700, ctr: 2.4, position: 10.8, positionChange: -1 },
  { query: "technical seo audit checklist", clicks: 58, impressions: 3400, ctr: 1.7, position: 13.6, positionChange: 2 },
  { query: "ai visibility score", clicks: 54, impressions: 1200, ctr: 4.5, position: 6.8, positionChange: 3 },
  { query: "google search console guide", clicks: 49, impressions: 6100, ctr: 0.8, position: 22.4, positionChange: -4 },
  { query: "saas marketing analytics platform", clicks: 43, impressions: 2900, ctr: 1.5, position: 17.9, positionChange: 0 },
  { query: "brand mention tracking tool", clicks: 38, impressions: 1600, ctr: 2.4, position: 9.7, positionChange: 1 },
  { query: "keyword position tracker", clicks: 34, impressions: 4200, ctr: 0.8, position: 19.3, positionChange: -2 },
  { query: "seo platform for agencies", clicks: 29, impressions: 3800, ctr: 0.8, position: 21.1, positionChange: 0 },
];

const MOCK_PAGES = [
  { query: "/blog/ai-seo-guide", clicks: 489, impressions: 8200, ctr: 6.0, position: 2.8, positionChange: 1 },
  { query: "/features/rank-tracking", clicks: 312, impressions: 5400, ctr: 5.8, position: 3.5, positionChange: 2 },
  { query: "/blog/content-gap-analysis", clicks: 241, impressions: 4700, ctr: 5.1, position: 4.2, positionChange: -1 },
  { query: "/pricing", clicks: 198, impressions: 3200, ctr: 6.2, position: 3.1, positionChange: 0 },
  { query: "/blog/ai-visibility-score", clicks: 167, impressions: 2900, ctr: 5.8, position: 4.8, positionChange: 3 },
  { query: "/features/ai-visibility", clicks: 143, impressions: 4100, ctr: 3.5, position: 7.4, positionChange: -2 },
  { query: "/", clicks: 128, impressions: 6800, ctr: 1.9, position: 11.2, positionChange: 1 },
  { query: "/blog/technical-seo-checklist", clicks: 112, impressions: 3300, ctr: 3.4, position: 8.7, positionChange: 0 },
  { query: "/blog/google-ads-roas", clicks: 96, impressions: 2600, ctr: 3.7, position: 9.1, positionChange: 2 },
  { query: "/integrations/google-search-console", clicks: 78, impressions: 2100, ctr: 3.7, position: 8.3, positionChange: 1 },
];

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
          data={activeTab === "queries" ? MOCK_QUERIES_EXTENDED : MOCK_PAGES}
          title={activeTab === "queries" ? "Top Queries" : "Top Pages"}
        />
      </div>
    </div>
  );
}

