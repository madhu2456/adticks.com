"use client";
import React, { useState } from "react";
import {
  Megaphone, Link2, DollarSign, MousePointerClick,
  TrendingUp, BarChart2, RefreshCw,
} from "lucide-react";
import { PerformanceChart } from "@/components/ads/PerformanceChart";
import { CampaignTable } from "@/components/ads/CampaignTable";
import { mockAdsPerformance, mockCampaigns } from "@/lib/mockData";

const EXTENDED_CAMPAIGNS = [
  { id: "1", name: "Brand Keywords", status: "active" as const, budget: 1500, spend: 1247, impressions: 182000, clicks: 3640, conversions: 48, cpc: 0.34, roas: 4.2, ctr: 2.0 },
  { id: "2", name: "Competitor Conquest", status: "active" as const, budget: 1000, spend: 892, impressions: 94000, clicks: 1880, conversions: 31, cpc: 0.47, roas: 3.8, ctr: 2.0 },
  { id: "3", name: "Product Features", status: "active" as const, budget: 800, spend: 756, impressions: 62000, clicks: 2170, conversions: 67, cpc: 0.35, roas: 6.1, ctr: 3.5 },
  { id: "4", name: "Remarketing", status: "paused" as const, budget: 2000, spend: 1380, impressions: 145000, clicks: 4060, conversions: 29, cpc: 0.34, roas: 2.9, ctr: 2.8 },
  { id: "5", name: "Display Prospecting", status: "paused" as const, budget: 600, spend: 410, impressions: 520000, clicks: 820, conversions: 8, cpc: 0.50, roas: 1.4, ctr: 0.2 },
];

function StatCard({ icon: Icon, label, value, sub, color = "#6366f1" }: {
  icon: React.ElementType;
  label: string;
  value: string;
  sub?: string;
  color?: string;
}) {
  return (
    <div className="bg-[#1e293b] rounded-xl border border-[#334155] p-5">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${color}18` }}>
          <Icon className="h-4 w-4" style={{ color }} />
        </div>
        <span className="text-xs text-[#94a3b8] font-medium">{label}</span>
      </div>
      <p className="text-2xl font-bold text-[#f1f5f9]">{value}</p>
      {sub && <p className="text-xs text-[#94a3b8] mt-1">{sub}</p>}
    </div>
  );
}

export default function AdsPage() {
  const [isConnected, setIsConnected] = useState(false);
  const [syncing, setSyncing] = useState(false);

  const totalSpend = mockAdsPerformance.reduce((s, d) => s + d.spend, 0);
  const totalClicks = mockAdsPerformance.reduce((s, d) => s + d.clicks, 0);
  const totalConversions = mockAdsPerformance.reduce((s, d) => s + d.conversions, 0);
  const avgROAS = (mockAdsPerformance.reduce((s, d) => s + d.roas, 0) / mockAdsPerformance.length).toFixed(1);
  const avgCPC = (mockAdsPerformance.reduce((s, d) => s + d.cpc, 0) / mockAdsPerformance.length).toFixed(2);

  function handleSync() {
    setSyncing(true);
    setTimeout(() => setSyncing(false), 2000);
  }

  if (!isConnected) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center p-6">
        <div className="max-w-lg w-full">
          <div className="bg-[#1e293b] rounded-2xl border border-[#334155] p-8 text-center">
            <div className="w-16 h-16 rounded-2xl bg-[#f97316]/10 border border-[#f97316]/20 flex items-center justify-center mx-auto mb-6">
              <Megaphone className="h-8 w-8 text-[#f97316]" />
            </div>
            <h2 className="text-xl font-bold text-[#f1f5f9] mb-2">Connect Google Ads</h2>
            <p className="text-[#94a3b8] text-sm mb-6 leading-relaxed">
              Link your Google Ads account to track spend, conversions, ROAS, and campaign performance side-by-side with your organic data.
            </p>

            <div className="grid grid-cols-2 gap-3 mb-8 text-left">
              {[
                { icon: DollarSign, label: "Spend Tracking", desc: "Daily budget & actual spend" },
                { icon: TrendingUp, label: "ROAS Monitoring", desc: "Return on ad spend trends" },
                { icon: MousePointerClick, label: "Conversion Data", desc: "Track goals and conversions" },
                { icon: BarChart2, label: "Campaign Compare", desc: "Multi-campaign analysis" },
              ].map(({ icon: Ic, label, desc }) => (
                <div key={label} className="flex items-start gap-3 bg-[#0f172a]/50 rounded-lg p-3">
                  <div className="w-7 h-7 rounded-md bg-[#f97316]/10 flex items-center justify-center shrink-0 mt-0.5">
                    <Ic className="h-3.5 w-3.5 text-[#f97316]" />
                  </div>
                  <div>
                    <p className="text-xs font-medium text-[#f1f5f9]">{label}</p>
                    <p className="text-xs text-[#94a3b8]">{desc}</p>
                  </div>
                </div>
              ))}
            </div>

            <button
              onClick={() => alert("Redirecting to Google Ads OAuth...")}
              className="w-full flex items-center justify-center gap-2 bg-[#f97316] hover:bg-[#ea6c0a] text-white font-semibold rounded-xl py-3 text-sm transition-colors shadow-lg shadow-[#f97316]/20 mb-3"
            >
              <Link2 className="h-4 w-4" />
              Connect Google Ads
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
          <h1 className="text-2xl font-bold text-[#f1f5f9]">Ads Performance</h1>
          <p className="text-sm text-[#94a3b8] mt-1">Google Ads · Last 30 days</p>
        </div>
        <button
          onClick={handleSync}
          disabled={syncing}
          className="flex items-center gap-2 bg-[#f97316]/10 hover:bg-[#f97316]/20 border border-[#f97316]/30 text-[#f97316] rounded-xl px-4 py-2 text-sm font-medium transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${syncing ? "animate-spin" : ""}`} />
          {syncing ? "Syncing..." : "Sync Google Ads"}
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard icon={DollarSign} label="Total Spend" value={`$${totalSpend.toLocaleString()}`} sub="Last 30 days" color="#f97316" />
        <StatCard icon={MousePointerClick} label="Clicks" value={totalClicks.toLocaleString()} sub="Total clicks" color="#6366f1" />
        <StatCard icon={TrendingUp} label="Conversions" value={totalConversions.toString()} sub="Total goals" color="#10b981" />
        <StatCard icon={BarChart2} label="Avg ROAS" value={`${avgROAS}x`} sub="Return on ad spend" color="#8b5cf6" />
        <StatCard icon={DollarSign} label="Avg CPC" value={`$${avgCPC}`} sub="Cost per click" color="#f59e0b" />
      </div>

      {/* Chart */}
      <PerformanceChart data={mockAdsPerformance} />

      {/* Campaigns */}
      <CampaignTable campaigns={EXTENDED_CAMPAIGNS} />
    </div>
  );
}
