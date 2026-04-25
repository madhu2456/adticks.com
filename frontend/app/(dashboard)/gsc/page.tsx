"use client";
import React, { useState, useEffect } from "react";
import {
  BarChart2, RefreshCw, Link2, MousePointerClick,
  Eye, Percent, Hash, TrendingUp, Zap, Check, ChevronRight,
  Globe, AlertCircle, Loader2
} from "lucide-react";
import { ScanModal } from "@/components/layout/ScanModal";
import { ImpressionsChart } from "@/components/gsc/ImpressionsChart";
import { CTRChart } from "@/components/gsc/CTRChart";
import { QueryTable } from "@/components/gsc/QueryTable";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { mockGSCQueries, mockGSCPages, mockGSCMetrics } from "@/lib/mockData";
import { useActiveProject } from "@/hooks/useProject";
import { useGSCQueries, useGSCMetrics, useGSCProperties } from "@/hooks/useGSC";
import { useAlertModal } from "@/hooks/useAlertModal";
import { api } from "@/lib/api";
import { useQueryClient } from "@tanstack/react-query";

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
  const { activeProject } = useActiveProject();
  const { showAlert, AlertModal } = useAlertModal();
  const queryClient = useQueryClient();
  
  const [activeTab, setActiveTab] = useState<"queries" | "pages">("queries");
  const [syncing, setSyncing] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [isScanModalOpen, setIsScanModalOpen] = useState(false);
  
  const isConnected = activeProject?.gsc_connected || false;

  // Data Hooks
  const { data: queriesData, isLoading: queriesLoading } = useGSCQueries(isConnected ? (activeProject?.id || "") : "");
  const { data: metricsData, isLoading: metricsLoading } = useGSCMetrics(isConnected ? (activeProject?.id || "") : "");
  const { data: properties, isLoading: propsLoading, error: propsError } = useGSCProperties();

  // Extract data from paginated responses
  const queries = (queriesData?.data || []) as any[];
  const metrics = (metricsData?.data || (isConnected ? [] : mockGSCMetrics)) as any[];

  const totalClicks = queries.reduce((s: number, q: any) => s + (q.clicks || 0), 0);
  const totalImpressions = metrics.reduce((s: number, m: any) => s + (m.impressions || 0), 0);
  const avgCTR = metrics.length > 0 ? (metrics.reduce((s: number, m: any) => s + (m.ctr || 0), 0) / metrics.length).toFixed(2) : "0";
  const avgPosition = metrics.length > 0 ? (metrics.reduce((s: number, m: any) => s + (m.position || 0), 0) / metrics.length).toFixed(1) : "0";

  async function handleConnect() {
    if (!activeProject) return;
    try {
      const { auth_url } = await api.gsc.getAuthUrl(activeProject.id);
      window.location.href = auth_url;
    } catch (err) {
      console.error("Failed to get GSC auth URL:", err);
      showAlert({
        title: "Connection Error",
        message: "Failed to connect to Google. Please try again.",
        type: "error",
      });
    }
  }

  async function handleSelectProperty(url: string) {
    if (!activeProject) return;
    setConnecting(true);
    try {
      await api.gsc.connectProperty(activeProject.id, url);
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      showAlert({
        title: "Connected!",
        message: `Successfully linked ${url} to your project.`,
        type: "success",
      });
    } catch (err) {
      console.error("Failed to connect property:", err);
    } finally {
      setConnecting(false);
    }
  }

  async function handleSync() {
    if (!activeProject) return;
    setIsScanModalOpen(true);
  }

  // If connected, show dashboard
  if (isConnected) {
    return (
      <div className="p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-[#f1f5f9]">Google Search Console</h1>
            <p className="text-sm text-[#94a3b8] mt-1 flex items-center gap-1">
              <Globe size={12} />
              {activeProject?.domain}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              onClick={handleSync}
              className="gap-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 border-0"
            >
              <Zap size={16} />
              Sync GSC Data
            </Button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {queriesLoading || metricsLoading ? (
            <>
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-24 w-full" />
            </>
          ) : (
            <>
              <StatCard icon={MousePointerClick} label="Total Clicks" value={totalClicks.toLocaleString()} sub="Last 28 days" />
              <StatCard icon={Eye} label="Total Impressions" value={totalImpressions.toLocaleString()} sub="Last 28 days" />
              <StatCard icon={Percent} label="Avg CTR" value={`${avgCTR}%`} sub="Click-through rate" />
              <StatCard icon={Hash} label="Avg Position" value={`#${avgPosition}`} sub="Search ranking" />
            </>
          )}
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          <div className="xl:col-span-2">
            {metricsLoading ? <Skeleton className="h-80 w-full" /> : <ImpressionsChart data={metrics} />}
          </div>
          <div>
            {metricsLoading ? <Skeleton className="h-80 w-full" /> : <CTRChart data={metrics} />}
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-[#1e293b] rounded-2xl border border-[#334155] overflow-hidden">
          <div className="p-4 border-b border-[#334155] flex items-center justify-between bg-[#1e293b]/50">
            <div className="flex gap-1 bg-[#0f172a] rounded-lg p-1 border border-[#334155]">
              {(["queries", "pages"] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium capitalize transition-colors ${
                    activeTab === tab
                      ? "bg-[#6366f1] text-white shadow"
                      : "text-[#94a3b8] hover:text-[#f1f5f9]"
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>
          </div>
          <div className="p-0">
            {queriesLoading ? (
              <div className="p-6 space-y-3">
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-full" />
              </div>
            ) : (
              <QueryTable
                data={queries}
                title={activeTab === "queries" ? "Top Queries" : "Top Pages"}
              />
            )}
          </div>
        </div>

        <ScanModal
          isOpen={isScanModalOpen}
          onClose={() => setIsScanModalOpen(false)}
          projectId={activeProject?.id}
          featureType="gsc"
        />
        {AlertModal}
      </div>
    );
  }

  // If not connected, show connection or property selection
  const hasToken = !!properties && Array.isArray(properties);

  return (
    <div className="min-h-[80vh] flex items-center justify-center p-6">
      <div className="max-w-xl w-full">
        {!hasToken ? (
          <div className="bg-[#1e293b] rounded-2xl border border-[#334155] p-8 text-center">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#6366f1]/20 to-[#8b5cf6]/20 border border-[#6366f1]/30 flex items-center justify-center mx-auto mb-6">
              <BarChart2 className="h-8 w-8 text-[#6366f1]" />
            </div>
            <h2 className="text-xl font-bold text-[#f1f5f9] mb-2">Connect Google Search Console</h2>
            <p className="text-[#94a3b8] text-sm mb-8 leading-relaxed">
              Unlock real search data. Link your Google account to track exactly how users find you on Google Search.
            </p>

            <div className="grid grid-cols-2 gap-3 mb-8 text-left">
              {[
                { icon: MousePointerClick, label: "Real Clicks", desc: "No more guessing" },
                { icon: TrendingUp, label: "True Rankings", desc: "Live SERP data" },
              ].map(({ icon: Ic, label, desc }) => (
                <div key={label} className="flex items-start gap-3 bg-[#0f172a]/50 rounded-lg p-3 border border-[#334155]/50">
                  <div className="w-7 h-7 rounded-md bg-[#6366f1]/10 flex items-center justify-center shrink-0 mt-0.5">
                    <Ic className="h-3.5 w-3.5 text-[#6366f1]" />
                  </div>
                  <div>
                    <p className="text-xs font-medium text-[#f1f5f9]">{label}</p>
                    <p className="text-[10px] text-[#94a3b8]">{desc}</p>
                  </div>
                </div>
              ))}
            </div>

            <Button
              onClick={handleConnect}
              size="lg"
              className="w-full gap-2 bg-[#6366f1] hover:bg-[#4f46e5] text-white rounded-xl h-12 shadow-lg shadow-[#6366f1]/20"
            >
              <Link2 size={18} />
              Sign in with Google
            </Button>
          </div>
        ) : (
          <div className="bg-[#1e293b] rounded-2xl border border-[#334155] p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-green-500/10 flex items-center justify-center">
                <Check className="h-5 w-5 text-green-500" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-[#f1f5f9]">Account Connected</h2>
                <p className="text-xs text-[#94a3b8]">Select a GSC Property to link to this project</p>
              </div>
            </div>

            <div className="space-y-2 max-h-[300px] overflow-y-auto pr-2 custom-scroll">
              {properties.map((prop: any) => (
                <button
                  key={prop.siteUrl}
                  onClick={() => handleSelectProperty(prop.siteUrl)}
                  disabled={connecting}
                  className="w-full flex items-center justify-between p-4 bg-[#0f172a]/50 hover:bg-[#0f172a] border border-[#334155] rounded-xl transition-all group"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-[#334155]/50 flex items-center justify-center">
                      <Globe size={14} className="text-[#94a3b8]" />
                    </div>
                    <span className="text-sm font-medium text-[#f1f5f9]">{prop.siteUrl}</span>
                  </div>
                  {connecting ? (
                    <Loader2 size={14} className="animate-spin text-[#94a3b8]" />
                  ) : (
                    <ChevronRight size={14} className="text-[#334155] group-hover:text-[#6366f1] transition-colors" />
                  )}
                </button>
              ))}
              
              {properties.length === 0 && (
                <div className="text-center py-8 bg-[#0f172a]/30 rounded-xl border border-dashed border-[#334155]">
                  <AlertCircle className="mx-auto h-8 w-8 text-[#94a3b8] mb-2 opacity-20" />
                  <p className="text-sm text-[#94a3b8]">No GSC properties found in this account.</p>
                </div>
              )}
            </div>
            
            <Button
              variant="ghost"
              onClick={handleConnect}
              className="w-full mt-4 text-xs text-[#94a3b8] hover:text-[#f1f5f9]"
            >
              Switch Google Account
            </Button>
          </div>
        )}
      </div>
      {AlertModal}
    </div>
  );
}
