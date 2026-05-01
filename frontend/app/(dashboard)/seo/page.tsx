"use client";
import React, { useState } from "react";
import { Badge } from "@/components/ui/badge";
import {
  Zap, RefreshCw, Search, ShieldCheck, FileSearch, Globe, Sparkles, Activity,
  ListChecks, Link2, FileText, MapPin, ScanText, FileDown, Layers, Network,
  AlertCircle, Grid, Mail, ChevronRight, ChevronDown, BarChart3
} from "lucide-react";
import { cn } from "@/lib/utils";

// Existing components
import { KeywordTable } from "@/components/seo/KeywordTable";
import { RankTracker } from "@/components/seo/RankTracker";
import { OnPageScore } from "@/components/seo/OnPageScore";
import { ContentGaps } from "@/components/seo/ContentGaps";
import { TechnicalSEO } from "@/components/seo/TechnicalSEO";
import { KeywordManager } from "@/components/seo/KeywordManager";
import { BacklinkDashboard } from "@/components/seo/BacklinkDashboard";
import { CompetitorAnalysis } from "@/components/seo/CompetitorAnalysis";

// New advanced components
import { SEOHubOverview } from "@/components/seo/SEOHubOverview";
import { SiteAuditDashboard } from "@/components/seo/SiteAuditDashboard";
import { CoreWebVitalsPanel } from "@/components/seo/CoreWebVitalsPanel";
import { KeywordMagicTool } from "@/components/seo/KeywordMagicTool";
import { SerpAnalyzer } from "@/components/seo/SerpAnalyzer";
import { BacklinkIntelligence } from "@/components/seo/BacklinkIntelligence";
import { ContentStudio } from "@/components/seo/ContentStudio";
import { LocalSEOSuite } from "@/components/seo/LocalSEOSuite";
import { LogFileAnalyzer } from "@/components/seo/LogFileAnalyzer";
import { ReportBuilder } from "@/components/seo/ReportBuilder";
// Gap-fill components
import { CannibalizationDetector } from "@/components/seo/CannibalizationDetector";
import { InternalLinksAnalyzer } from "@/components/seo/InternalLinksAnalyzer";
import { DomainCompare } from "@/components/seo/DomainCompare";
import { ToolsHub } from "@/components/seo/ToolsHub";
import { OutreachTracker } from "@/components/seo/OutreachTracker";
import { SnippetVolatility } from "@/components/seo/SnippetVolatility";

import { ScanModal } from "@/components/layout/ScanModal";
import { useActiveProject } from "@/hooks/useProject";
import { useKeywords, useContentGaps, useTechnicalChecks } from "@/hooks/useSEO";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";

type FeatureKey =
  | 'seo' | 'ai' | 'geo' | 'gsc' | 'ads' | 'keywords_gsc'
  | 'on_page' | 'technical' | 'gaps';

interface NavItem {
  title: string;
  value: string;
  icon: any;
  isNew?: boolean;
}

interface NavCategory {
  title: string;
  items: NavItem[];
}

const SEO_NAV: NavCategory[] = [
  {
    title: "Dashboard",
    items: [
      { title: "Overview", value: "overview", icon: BarChart3 },
    ]
  },
  {
    title: "Domain Analysis",
    items: [
      { title: "Site Audit", value: "audit", icon: ShieldCheck, isNew: true },
      { title: "Technical SEO", value: "technical", icon: ListChecks },
      { title: "Core Web Vitals", value: "cwv", icon: Activity, isNew: true },
      { title: "Log File Analyzer", value: "logs", icon: ScanText, isNew: true },
      { title: "Internal Links", value: "internal-links", icon: Network, isNew: true },
      { title: "Cannibalization", value: "cannibalization", icon: Layers, isNew: true },
    ]
  },
  {
    title: "Keyword Research",
    items: [
      { title: "Keyword Magic", value: "keyword-magic", icon: Sparkles, isNew: true },
      { title: "Keyword Discovery", value: "keywords", icon: Search },
      { title: "Topic Clusters", value: "clusters", icon: Layers },
      { title: "Content Gaps", value: "gaps", icon: FileSearch },
      { title: "Snippet Volatility", value: "snippets", icon: AlertCircle, isNew: true },
    ]
  },
  {
    title: "Rank Tracking",
    items: [
      { title: "Rank Tracker", value: "rankings", icon: Activity },
      { title: "SERP Analyzer", value: "serp", icon: ListChecks, isNew: true },
    ]
  },
  {
    title: "Link Building",
    items: [
      { title: "Backlink Analytics", value: "backlinks", icon: Link2 },
      { title: "Backlink Intelligence", value: "backlink-intel", icon: Link2, isNew: true },
      { title: "Outreach Tracker", value: "outreach", icon: Mail, isNew: true },
    ]
  },
  {
    title: "Content & Local",
    items: [
      { title: "On-Page Audit", value: "onpage", icon: ScanText },
      { title: "Content Studio", value: "content-studio", icon: FileText, isNew: true },
      { title: "Local SEO", value: "local", icon: MapPin, isNew: true },
    ]
  },
  {
    title: "Reporting & Tools",
    items: [
      { title: "Report Builder", value: "reports", icon: FileDown, isNew: true },
      { title: "Compare Domains", value: "compare", icon: Globe, isNew: true },
      { title: "Tools Hub", value: "tools", icon: Grid, isNew: true },
    ]
  }
];

export default function SEOPage() {
  const { activeProject } = useActiveProject();
  const [activeTab, setActiveTab] = useState("overview");
  const [search, setSearch] = useState("");
  const [isScanModalOpen, setIsScanModalOpen] = useState(false);
  const [currentFeature, setCurrentFeature] = useState<FeatureKey>('seo');
  const [expandedCategories, setExpandedCategories] = useState<string[]>(SEO_NAV.map(c => c.title));

  const { data: keywordResponse, isLoading: keywordsLoading, refetch: refetchKeywords } =
    useKeywords(activeProject?.id || "", search);
  const { data: gapsResponse, isLoading: gapsLoading, refetch: refetchGaps } =
    useContentGaps(activeProject?.id || "");
  const { data: technicalResponse, isLoading: technicalLoading, refetch: refetchTechnical } =
    useTechnicalChecks(activeProject?.id || "");

  const keywords = (keywordResponse?.data || []) as any[];
  const gaps = Array.isArray(gapsResponse) ? gapsResponse : (gapsResponse?.data || []) as any[];
  const technicalChecks = (technicalResponse?.data || []) as any[];

  const filteredKeywords = keywords.filter((k) =>
    search ? (k.keyword || "").toLowerCase().includes(search.toLowerCase()) : true
  );

  const triggerScan = (feature: FeatureKey) => {
    setCurrentFeature(feature);
    setIsScanModalOpen(true);
  };

  const handleModalClose = () => {
    setIsScanModalOpen(false);
    if (currentFeature === 'seo' || currentFeature === 'keywords_gsc') refetchKeywords();
    if (currentFeature === 'technical') refetchTechnical();
    if (currentFeature === 'gaps') refetchGaps();
  };

  const toggleCategory = (title: string) => {
    setExpandedCategories(prev => 
      prev.includes(title) ? prev.filter(t => t !== title) : [...prev, title]
    );
  };

  if (!activeProject) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <p className="text-text-muted text-lg">Please select a project to view SEO data.</p>
      </div>
    );
  }

  const projectId = activeProject.id;
  const projectUrl = activeProject.domain || activeProject.url || "";

  return (
    <div className="flex h-[calc(100vh-120px)] overflow-hidden bg-background -m-6 rounded-xl border border-border shadow-sm">
      {/* Internal Navigation Sidebar */}
      <aside className="w-64 border-r border-border bg-card/30 flex flex-col shrink-0 overflow-hidden">
        <div className="p-4 border-b border-border flex items-center justify-between bg-card/50">
          <h2 className="font-bold text-sm uppercase tracking-wider text-text-muted px-2">SEO Suite</h2>
          <Badge variant="outline" className="text-[10px] h-5 px-1.5 border-primary/20 text-primary bg-primary/5">PRO</Badge>
        </div>
        
        <div className="flex-1 overflow-y-auto custom-scrollbar p-3 space-y-4">
          {SEO_NAV.map((category) => (
            <div key={category.title} className="space-y-1">
              <button 
                onClick={() => toggleCategory(category.title)}
                className="w-full flex items-center justify-between px-2 py-1.5 text-xs font-semibold text-text-muted hover:text-text-primary transition-colors group"
              >
                <span>{category.title}</span>
                {expandedCategories.includes(category.title) ? <ChevronDown size={14}/> : <ChevronRight size={14}/>}
              </button>
              
              {expandedCategories.includes(category.title) && (
                <div className="space-y-0.5 ml-1 border-l-2 border-border/40 pl-1">
                  {category.items.map((item) => {
                    const Icon = item.icon;
                    const isActive = activeTab === item.value;
                    return (
                      <button
                        key={item.value}
                        onClick={() => setActiveTab(item.value)}
                        className={cn(
                          "w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-all group relative",
                          isActive 
                            ? "bg-primary/10 text-primary font-medium border border-primary/10" 
                            : "text-text-muted hover:bg-card-hover hover:text-text-primary border border-transparent"
                        )}
                      >
                        <Icon size={16} className={cn(isActive ? "text-primary" : "text-text-muted group-hover:text-text-primary")}/>
                        <span className="truncate flex-1 text-left">{item.title}</span>
                        {item.isNew && !isActive && (
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse shrink-0"/>
                        )}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="p-4 bg-card/50 border-t border-border space-y-3">
          <div className="p-3 rounded-xl bg-gradient-to-br from-indigo-600/10 to-purple-600/10 border border-indigo-500/20">
            <p className="text-xs text-text-muted mb-2 font-medium">Domain Health</p>
            <div className="flex items-center gap-2">
              <div className="h-1.5 flex-1 bg-border rounded-full overflow-hidden">
                <div className="h-full bg-indigo-500 w-[78%]"/>
              </div>
              <span className="text-[10px] font-bold text-indigo-600">78%</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-hidden bg-background">
        {/* Local Sticky Header */}
        <header className="h-14 border-b border-border bg-card/50 backdrop-blur-md px-6 flex items-center justify-between shrink-0 sticky top-0 z-10">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-primary/10 text-primary flex items-center justify-center">
              {(() => {
                const navItem = SEO_NAV.flatMap(c => c.items).find(i => i.value === activeTab);
                const Icon = navItem?.icon || Globe;
                return <Icon size={18}/>;
              })()}
            </div>
            <div>
              <h1 className="text-sm font-bold text-text-primary">
                {SEO_NAV.flatMap(c => c.items).find(i => i.value === activeTab)?.title}
              </h1>
              <p className="text-[10px] text-text-muted uppercase tracking-wider font-medium">
                {projectUrl}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
             <div className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-border/40 text-text-muted text-[11px] font-medium mr-2">
                <Activity size={12} className="text-emerald-500"/>
                <span>Real-time Monitoring Active</span>
             </div>
             <div className="relative group">
               <Button
                  size="sm"
                  className="gap-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 border-0 shadow-lg shadow-indigo-500/20 h-9 px-4"
                >
                  <Zap size={14} />
                  Scan
                  <ChevronDown size={12} className="group-hover:rotate-180 transition-transform" />
                </Button>
                <div className="absolute right-0 mt-2 w-48 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all bg-[#1e293b] border border-[#334155] z-50">
                  <button
                    onClick={() => triggerScan('seo')}
                    className="w-full text-left px-4 py-2.5 text-[13px] font-medium text-text-2 hover:text-text-1 hover:bg-white/[0.05] transition-all first:rounded-t-lg flex items-center gap-2"
                  >
                    <ShieldCheck size={13} className="text-indigo-400" />
                    SEO Audit
                  </button>
                  <button
                    onClick={() => triggerScan('on_page')}
                    className="w-full text-left px-4 py-2.5 text-[13px] font-medium text-text-2 hover:text-text-1 hover:bg-white/[0.05] transition-all flex items-center gap-2"
                  >
                    <FileSearch size={13} className="text-purple-400" />
                    On-Page Audit
                  </button>
                  <button
                    onClick={() => triggerScan('technical')}
                    className="w-full text-left px-4 py-2.5 text-[13px] font-medium text-text-2 hover:text-text-1 hover:bg-white/[0.05] transition-all flex items-center gap-2"
                  >
                    <ListChecks size={13} className="text-blue-400" />
                    Technical Audit
                  </button>
                  <button
                    onClick={() => triggerScan('gaps')}
                    className="w-full text-left px-4 py-2.5 text-[13px] font-medium text-text-2 hover:text-text-1 hover:bg-white/[0.05] transition-all last:rounded-b-lg flex items-center gap-2"
                  >
                    <FileSearch size={13} className="text-emerald-400" />
                    Content Gaps
                  </button>
                </div>
              </div>
          </div>
        </header>

        {/* Content Scroll Area */}
        <div className="flex-1 overflow-y-auto p-6 custom-scrollbar bg-slate-50/30 dark:bg-transparent">
          <div className="max-w-[1600px] mx-auto space-y-6 animate-in fade-in duration-500">
            {activeTab === "overview" && (
              <div className="space-y-6">
                <SEOHubOverview projectId={projectId}/>
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="p-4 rounded-xl border border-border bg-card shadow-sm space-y-4">
                    <h3 className="text-sm font-bold text-text-primary flex items-center gap-2">
                      <Zap size={16} className="text-amber-500"/>
                      Quick Actions
                    </h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <QuickAction icon={ShieldCheck} label="Site Audit" onClick={() => setActiveTab("audit")}/>
                      <QuickAction icon={Activity} label="Web Vitals" onClick={() => setActiveTab("cwv")}/>
                      <QuickAction icon={Sparkles} label="Keywords" onClick={() => setActiveTab("keyword-magic")}/>
                      <QuickAction icon={Network} label="Link Intel" onClick={() => setActiveTab("backlink-intel")}/>
                    </div>
                  </div>
                  <div className="p-4 rounded-xl border border-border bg-card shadow-sm space-y-4">
                    <h3 className="text-sm font-bold text-text-primary flex items-center gap-2">
                      <FileText size={16} className="text-indigo-500"/>
                      Content & Reporting
                    </h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <QuickAction icon={FileText} label="Content Studio" onClick={() => setActiveTab("content-studio")}/>
                      <QuickAction icon={Layers} label="Topic Clusters" onClick={() => setActiveTab("clusters")}/>
                      <QuickAction icon={MapPin} label="Local SEO" onClick={() => setActiveTab("local")}/>
                      <QuickAction icon={FileDown} label="Reports" onClick={() => setActiveTab("reports")}/>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === "audit" && <SiteAuditDashboard projectId={projectId} defaultUrl={projectUrl}/>}
            {activeTab === "cwv" && <CoreWebVitalsPanel projectId={projectId} defaultUrl={projectUrl}/>}
            {activeTab === "keyword-magic" && <KeywordMagicTool projectId={projectId}/>}
            {activeTab === "serp" && <SerpAnalyzer projectId={projectId}/>}
            {activeTab === "rankings" && <RankTracker projectId={projectId} />}
            
            {activeTab === "keywords" && (
              <div className="space-y-4">
                <div className="flex justify-between items-center bg-card p-4 rounded-xl border border-border shadow-sm">
                  <div className="flex items-center gap-2">
                    <h2 className="text-lg font-semibold text-text-primary">Keyword Discovery</h2>
                    <Badge className="bg-indigo-500/10 text-indigo-600 border border-indigo-500/20 font-medium">AI Powered</Badge>
                  </div>
                  <div className="flex gap-2">
                    <Button onClick={() => triggerScan('keywords_gsc')} variant="outline" size="sm" className="gap-2 h-9">
                      <Globe size={14}/> Sync from GSC
                    </Button>
                    <Button onClick={() => triggerScan('seo')} variant="outline" size="sm" className="gap-2 h-9 border-primary/20 hover:border-primary/40 hover:bg-primary/5">
                      <RefreshCw size={14} className={keywordsLoading ? "animate-spin" : ""}/> Refresh AI Keywords
                    </Button>
                  </div>
                </div>
                {keywordsLoading ? (
                  <div className="space-y-4">
                    <Skeleton className="h-12 w-full rounded-xl"/>
                    <Skeleton className="h-64 w-full rounded-xl"/>
                  </div>
                ) : (
                  <KeywordTable keywords={filteredKeywords} onSearch={setSearch}/>
                )}
              </div>
            )}

            {activeTab === "clusters" && <KeywordManager projectId={projectId}/>}

            {activeTab === "onpage" && (
              <div className="space-y-4">
                <div className="flex items-center gap-2 p-4 bg-card rounded-xl border border-border shadow-sm">
                  <h2 className="text-lg font-semibold text-text-primary">On-Page Audit</h2>
                  <Badge className="bg-indigo-500/10 text-indigo-600 border border-indigo-500/20 font-medium">AI Insights</Badge>
                </div>
                <OnPageScore projectId={projectId}/>
              </div>
            )}

            {activeTab === "content-studio" && <ContentStudio projectId={projectId}/>}
            {activeTab === "backlinks" && <BacklinkDashboard projectId={projectId}/>}
            {activeTab === "backlink-intel" && <BacklinkIntelligence projectId={projectId}/>}
            {activeTab === "competitors" && <CompetitorAnalysis projectId={projectId}/>}

            {activeTab === "gaps" && (
              <div className="space-y-4">
                <div className="flex justify-between items-center bg-card p-4 rounded-xl border border-border shadow-sm">
                  <div>
                    <div className="flex items-center gap-2 mb-0.5">
                      <h2 className="text-lg font-semibold text-text-primary">Content Gaps</h2>
                      <Badge className="bg-indigo-500/10 text-indigo-600 border border-indigo-500/20 font-medium">AI Engine</Badge>
                    </div>
                    <p className="text-xs text-text-muted">Topics your competitors rank for but you don&apos;t</p>
                  </div>
                  <Button onClick={() => triggerScan('gaps')} variant="outline" size="sm" className="gap-2 h-9 border-indigo-500/20 hover:border-indigo-500/40 hover:bg-indigo-500/5">
                    <FileSearch size={14} className={gapsLoading ? "animate-spin" : ""}/> Find Gaps
                  </Button>
                </div>
                {gapsLoading ? <Skeleton className="h-64 w-full rounded-xl"/> : <ContentGaps gaps={gaps || []}/>}
              </div>
            )}

            {activeTab === "technical" && (
              <div className="space-y-4">
                <div className="flex justify-between items-center bg-card p-4 rounded-xl border border-border shadow-sm">
                  <div>
                    <div className="flex items-center gap-2 mb-0.5">
                      <h2 className="text-lg font-semibold text-text-primary">Technical Audit</h2>
                      <Badge className="bg-success-500/10 text-success-600 border border-success-500/20 font-medium">Automated</Badge>
                    </div>
                    <p className="text-xs text-text-muted">Core technical health checks for your domain</p>
                  </div>
                  <Button onClick={() => triggerScan('technical')} variant="outline" size="sm" className="gap-2 h-9 border-success/20 hover:border-success/40 hover:bg-success/5">
                    <ShieldCheck size={14} className={technicalLoading ? "animate-spin" : ""}/> Run Audit
                  </Button>
                </div>
                {technicalLoading ? <Skeleton className="h-64 w-full rounded-xl"/> : <TechnicalSEO projectId={projectId} checks={technicalChecks || []}/>}
              </div>
            )}

            {activeTab === "local" && <LocalSEOSuite projectId={projectId}/>}
            {activeTab === "logs" && <LogFileAnalyzer projectId={projectId}/>}
            {activeTab === "reports" && <ReportBuilder projectId={projectId}/>}
            {activeTab === "cannibalization" && <CannibalizationDetector projectId={projectId}/>}
            {activeTab === "internal-links" && <InternalLinksAnalyzer projectId={projectId}/>}
            {activeTab === "compare" && <DomainCompare projectId={projectId} defaultDomain={projectUrl}/>}
            {activeTab === "tools" && <ToolsHub projectId={projectId}/>}
            {activeTab === "outreach" && <OutreachTracker projectId={projectId}/>}
            {activeTab === "snippets" && <SnippetVolatility projectId={projectId}/>}
          </div>
        </div>
      </main>

      <ScanModal
        isOpen={isScanModalOpen}
        onClose={handleModalClose}
        projectId={activeProject?.id}
        featureType={currentFeature}
      />

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 5px;
          height: 5px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(100, 116, 139, 0.1);
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(100, 116, 139, 0.2);
        }
      `}</style>
    </div>
  );
}

function QuickAction({ icon: Icon, label, onClick }: { icon: any; label: string; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="w-full text-left p-3 rounded-xl border border-border bg-card hover:bg-card-hover hover:border-primary/40 transition-all flex items-center gap-3 group"
    >
      <div className="w-9 h-9 rounded-lg bg-primary/5 text-primary flex items-center justify-center group-hover:bg-primary group-hover:text-white transition-colors">
        <Icon size={18}/>
      </div>
      <span className="text-xs font-semibold text-text-primary">{label}</span>
    </button>
  );
}
