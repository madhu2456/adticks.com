"use client";
import React, { useState } from "react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import {
  Zap, RefreshCw, Search, ShieldCheck, FileSearch, Globe, Sparkles, Activity,
  ListChecks, Link2, FileText, MapPin, ScanText, FileDown, Layers, Network,
  AlertCircle,
} from "lucide-react";

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
  | 'seo' | 'ai' | 'geo' | 'gsc' | 'ads' | 'full' | 'keywords_gsc'
  | 'on_page' | 'technical' | 'gaps';

export default function SEOPage() {
  const { activeProject } = useActiveProject();
  const [tab, setTab] = useState("overview");
  const [search, setSearch] = useState("");
  const [isScanModalOpen, setIsScanModalOpen] = useState(false);
  const [currentFeature, setCurrentFeature] = useState<FeatureKey>('seo');

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

  if (!activeProject) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <p className="text-text-muted">Please select a project to view SEO data.</p>
      </div>
    );
  }

  const projectId = activeProject.id;
  const projectUrl = activeProject.domain || activeProject.url || "";

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">SEO Hub</h1>
          <p className="text-text-muted text-sm mt-1">
            Complete SEO suite — site audit, keywords, backlinks, content, local, logs, reports
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            onClick={() => triggerScan('full')}
            className="gap-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 border-0 shadow-lg shadow-indigo-500/20"
          >
            <Zap size={16} />
            Run Full SEO Scan
          </Button>
        </div>
      </div>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList className="overflow-x-auto flex-nowrap whitespace-nowrap">
          <TabsTrigger value="overview" className="gap-1.5">
            <Globe size={13}/> Overview
          </TabsTrigger>
          <TabsTrigger value="audit" className="gap-1.5">
            <ShieldCheck size={13}/> Site Audit
            <Badge className="h-4 px-1 text-[8px] bg-emerald-500 text-white border-0">New</Badge>
          </TabsTrigger>
          <TabsTrigger value="cwv" className="gap-1.5">
            <Activity size={13}/> Web Vitals
            <Badge className="h-4 px-1 text-[8px] bg-emerald-500 text-white border-0">New</Badge>
          </TabsTrigger>
          <TabsTrigger value="keyword-magic" className="gap-1.5">
            <Sparkles size={13}/> Keyword Magic
            <Badge className="h-4 px-1 text-[8px] bg-emerald-500 text-white border-0">New</Badge>
          </TabsTrigger>
          <TabsTrigger value="serp" className="gap-1.5">
            <ListChecks size={13}/> SERP Analyzer
            <Badge className="h-4 px-1 text-[8px] bg-emerald-500 text-white border-0">New</Badge>
          </TabsTrigger>
          <TabsTrigger value="rankings" className="gap-1.5">Rankings</TabsTrigger>
          <TabsTrigger value="keywords" className="gap-1.5">Keywords</TabsTrigger>
          <TabsTrigger value="clusters" className="gap-1.5">Clusters</TabsTrigger>
          <TabsTrigger value="onpage" className="gap-1.5">On-Page</TabsTrigger>
          <TabsTrigger value="content-studio" className="gap-1.5">
            <FileText size={13}/> Content
            <Badge className="h-4 px-1 text-[8px] bg-emerald-500 text-white border-0">New</Badge>
          </TabsTrigger>
          <TabsTrigger value="backlinks" className="gap-1.5">Backlinks</TabsTrigger>
          <TabsTrigger value="backlink-intel" className="gap-1.5">
            <Link2 size={13}/> Link Intel
            <Badge className="h-4 px-1 text-[8px] bg-emerald-500 text-white border-0">New</Badge>
          </TabsTrigger>
          <TabsTrigger value="competitors" className="gap-1.5">Competitors</TabsTrigger>
          <TabsTrigger value="gaps" className="gap-1.5">Content Gaps</TabsTrigger>
          <TabsTrigger value="technical" className="gap-1.5">Technical</TabsTrigger>
          <TabsTrigger value="local" className="gap-1.5">
            <MapPin size={13}/> Local
            <Badge className="h-4 px-1 text-[8px] bg-emerald-500 text-white border-0">New</Badge>
          </TabsTrigger>
          <TabsTrigger value="logs" className="gap-1.5">
            <ScanText size={13}/> Logs
            <Badge className="h-4 px-1 text-[8px] bg-emerald-500 text-white border-0">New</Badge>
          </TabsTrigger>
          <TabsTrigger value="reports" className="gap-1.5">
            <FileDown size={13}/> Reports
            <Badge className="h-4 px-1 text-[8px] bg-emerald-500 text-white border-0">New</Badge>
          </TabsTrigger>
          <TabsTrigger value="cannibalization" className="gap-1.5">
            Cannibalization
            <Badge className="h-4 px-1 text-[8px] bg-emerald-500 text-white border-0">New</Badge>
          </TabsTrigger>
          <TabsTrigger value="internal-links" className="gap-1.5">
            Internal Links
            <Badge className="h-4 px-1 text-[8px] bg-emerald-500 text-white border-0">New</Badge>
          </TabsTrigger>
          <TabsTrigger value="compare" className="gap-1.5">
            Compare
            <Badge className="h-4 px-1 text-[8px] bg-emerald-500 text-white border-0">New</Badge>
          </TabsTrigger>
          <TabsTrigger value="tools" className="gap-1.5">
            Tools
            <Badge className="h-4 px-1 text-[8px] bg-emerald-500 text-white border-0">New</Badge>
          </TabsTrigger>
          <TabsTrigger value="outreach" className="gap-1.5">
            Outreach
            <Badge className="h-4 px-1 text-[8px] bg-emerald-500 text-white border-0">New</Badge>
          </TabsTrigger>
          <TabsTrigger value="snippets" className="gap-1.5">
            Snippets
            <Badge className="h-4 px-1 text-[8px] bg-emerald-500 text-white border-0">New</Badge>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <SEOHubOverview projectId={projectId}/>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-text-primary">Quick actions</h3>
              <QuickAction icon={ShieldCheck} label="Run a fresh site audit" onClick={() => setTab("audit")}/>
              <QuickAction icon={Activity} label="Test Core Web Vitals" onClick={() => setTab("cwv")}/>
              <QuickAction icon={Sparkles} label="Discover keyword ideas" onClick={() => setTab("keyword-magic")}/>
              <QuickAction icon={Network} label="Find link opportunities" onClick={() => setTab("backlink-intel")}/>
            </div>
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-text-primary">Content & reporting</h3>
              <QuickAction icon={FileText} label="Generate content brief" onClick={() => setTab("content-studio")}/>
              <QuickAction icon={Layers} label="Build a topic cluster" onClick={() => setTab("content-studio")}/>
              <QuickAction icon={MapPin} label="Local SEO consistency" onClick={() => setTab("local")}/>
              <QuickAction icon={FileDown} label="Build a white-label report" onClick={() => setTab("reports")}/>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="audit">
          <SiteAuditDashboard projectId={projectId} defaultUrl={projectUrl}/>
        </TabsContent>

        <TabsContent value="cwv">
          <CoreWebVitalsPanel projectId={projectId} defaultUrl={projectUrl}/>
        </TabsContent>

        <TabsContent value="keyword-magic">
          <KeywordMagicTool projectId={projectId}/>
        </TabsContent>

        <TabsContent value="serp">
          <SerpAnalyzer projectId={projectId}/>
        </TabsContent>

        <TabsContent value="rankings">
          <RankTracker projectId={projectId} />
        </TabsContent>

        <TabsContent value="keywords" className="space-y-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-semibold text-text-primary">Keyword Discovery</h2>
              <Badge className="bg-indigo-500/20 text-indigo-700 border border-indigo-500/30">Uses AI</Badge>
            </div>
            <div className="flex gap-2">
              <Button onClick={() => triggerScan('keywords_gsc')} variant="outline" size="sm" className="gap-2 border-indigo-500/20 hover:border-indigo-500/40">
                <Globe size={14}/> Sync from GSC
              </Button>
              <Button onClick={() => triggerScan('seo')} variant="outline" size="sm" className="gap-2 border-primary/20 hover:border-primary/40">
                <RefreshCw size={14} className={keywordsLoading ? "animate-spin" : ""}/> Refresh AI Keywords
              </Button>
            </div>
          </div>
          {keywordsLoading ? (
            <div className="space-y-4">
              <Skeleton className="h-12 w-full"/>
              <Skeleton className="h-64 w-full"/>
            </div>
          ) : (
            <KeywordTable keywords={filteredKeywords} onSearch={setSearch}/>
          )}
        </TabsContent>

        <TabsContent value="clusters">
          <KeywordManager projectId={projectId}/>
        </TabsContent>

        <TabsContent value="onpage">
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-semibold text-text-primary">On-Page Audit</h2>
              <Badge className="bg-indigo-500/20 text-indigo-700 border border-indigo-500/30">Uses AI</Badge>
            </div>
            <OnPageScore projectId={projectId}/>
          </div>
        </TabsContent>

        <TabsContent value="content-studio">
          <ContentStudio projectId={projectId}/>
        </TabsContent>

        <TabsContent value="backlinks">
          <BacklinkDashboard projectId={projectId}/>
        </TabsContent>

        <TabsContent value="backlink-intel">
          <BacklinkIntelligence projectId={projectId}/>
        </TabsContent>

        <TabsContent value="competitors">
          <CompetitorAnalysis projectId={projectId}/>
        </TabsContent>

        <TabsContent value="gaps" className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <h2 className="text-lg font-semibold text-text-primary">Content Gaps</h2>
                <Badge className="bg-indigo-500/20 text-indigo-700 border border-indigo-500/30">Uses AI</Badge>
              </div>
              <p className="text-sm text-text-muted">Topics your competitors rank for but you don&apos;t</p>
            </div>
            <Button onClick={() => triggerScan('gaps')} variant="outline" size="sm" className="gap-2 border-indigo-500/20 hover:border-indigo-500/40">
              <FileSearch size={14} className={gapsLoading ? "animate-spin" : ""}/> Find Gaps
            </Button>
          </div>
          {gapsLoading ? <Skeleton className="h-64 w-full"/> : <ContentGaps gaps={gaps || []}/>}
        </TabsContent>

        <TabsContent value="technical" className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <h2 className="text-lg font-semibold text-text-primary">Technical Audit</h2>
                <Badge className="bg-indigo-500/20 text-indigo-700 border border-indigo-500/30">Uses AI</Badge>
              </div>
              <p className="text-sm text-text-muted">Core technical health checks for your domain</p>
            </div>
            <Button onClick={() => triggerScan('technical')} variant="outline" size="sm" className="gap-2 border-success/20 hover:border-success/40">
              <ShieldCheck size={14} className={technicalLoading ? "animate-spin" : ""}/> Run Technical Audit
            </Button>
          </div>
          {technicalLoading ? <Skeleton className="h-64 w-full"/> : <TechnicalSEO projectId={projectId} checks={technicalChecks || []}/>}
        </TabsContent>

        <TabsContent value="local">
          <LocalSEOSuite projectId={projectId}/>
        </TabsContent>

        <TabsContent value="logs">
          <LogFileAnalyzer projectId={projectId}/>
        </TabsContent>

        <TabsContent value="reports">
          <ReportBuilder projectId={projectId}/>
        </TabsContent>

        <TabsContent value="cannibalization">
          <CannibalizationDetector projectId={projectId}/>
        </TabsContent>

        <TabsContent value="internal-links">
          <InternalLinksAnalyzer projectId={projectId}/>
        </TabsContent>

        <TabsContent value="compare">
          <DomainCompare projectId={projectId} defaultDomain={projectUrl}/>
        </TabsContent>

        <TabsContent value="tools">
          <ToolsHub projectId={projectId}/>
        </TabsContent>

        <TabsContent value="outreach">
          <OutreachTracker projectId={projectId}/>
        </TabsContent>

        <TabsContent value="snippets">
          <SnippetVolatility projectId={projectId}/>
        </TabsContent>
      </Tabs>

      <ScanModal
        isOpen={isScanModalOpen}
        onClose={handleModalClose}
        projectId={activeProject?.id}
        featureType={currentFeature}
      />
    </div>
  );
}

function QuickAction({ icon: Icon, label, onClick }: { icon: any; label: string; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="w-full text-left p-3 rounded-lg border bg-card hover:bg-card-hover hover:border-primary/40 transition flex items-center gap-3"
    >
      <div className="w-8 h-8 rounded bg-primary/10 text-primary flex items-center justify-center">
        <Icon size={16}/>
      </div>
      <span className="text-sm font-medium">{label}</span>
    </button>
  );
}
