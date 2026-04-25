"use client";
import React, { useState } from "react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Zap, RefreshCw, Search, ShieldCheck, FileSearch, Globe } from "lucide-react";
import { KeywordTable } from "@/components/seo/KeywordTable";
import { RankTracker } from "@/components/seo/RankTracker";
import { OnPageScore } from "@/components/seo/OnPageScore";
import { ContentGaps } from "@/components/seo/ContentGaps";
import { TechnicalSEO } from "@/components/seo/TechnicalSEO";
import { BacklinkDashboard } from "@/components/seo/BacklinkDashboard";
import { CompetitorAnalysis } from "@/components/seo/CompetitorAnalysis";
import { ScanModal } from "@/components/layout/ScanModal";
import { useActiveProject } from "@/hooks/useProject";
import { useKeywords, useContentGaps, useTechnicalChecks } from "@/hooks/useSEO";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";

export default function SEOPage() {
  const { activeProject } = useActiveProject();
  const [tab, setTab] = useState("keywords");
  const [search, setSearch] = useState("");
  const [isScanModalOpen, setIsScanModalOpen] = useState(false);
  const [currentFeature, setCurrentFeature] = useState<'seo' | 'ai' | 'geo' | 'gsc' | 'ads' | 'full' | 'keywords_gsc' | 'on_page' | 'technical' | 'gaps'>('seo');

  // Fetch real data from backend
  const { data: keywordResponse, isLoading: keywordsLoading, refetch: refetchKeywords } = useKeywords(activeProject?.id || "", search);
  const { data: gapsResponse, isLoading: gapsLoading, refetch: refetchGaps } = useContentGaps(activeProject?.id || "");
  const { data: technicalResponse, isLoading: technicalLoading, refetch: refetchTechnical } = useTechnicalChecks(activeProject?.id || "");

  // Extract data from paginated responses
  const keywords = (keywordResponse?.data || []) as any[];
  const gaps = (gapsResponse?.data || []) as any[];
  const technicalChecks = (technicalResponse?.data || []) as any[];

  const filteredKeywords = keywords.filter((k) =>
    search ? k.keyword?.toLowerCase().includes(search.toLowerCase()) : true
  );

  const triggerScan = (feature: 'seo' | 'technical' | 'gaps' | 'full' | 'keywords_gsc') => {
    setCurrentFeature(feature as any);
    setIsScanModalOpen(true);
  };

  const handleModalClose = () => {
    setIsScanModalOpen(false);
    // Refresh data based on which scan was run
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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">SEO Hub</h1>
          <p className="text-text-muted text-sm mt-1">Track rankings, audit pages, and discover content opportunities</p>
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
        <TabsList className="overflow-x-auto">
          <TabsTrigger value="keywords">Keywords</TabsTrigger>
          <TabsTrigger value="rankings">Rankings</TabsTrigger>
          <TabsTrigger value="onpage">On-Page</TabsTrigger>
          <TabsTrigger value="backlinks">Backlinks</TabsTrigger>
          <TabsTrigger value="competitors">Competitors</TabsTrigger>
          <TabsTrigger value="gaps">Content Gaps</TabsTrigger>
          <TabsTrigger value="technical">Technical</TabsTrigger>
        </TabsList>

        <TabsContent value="keywords" className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold text-text-primary">Keyword Discovery</h2>
            <div className="flex gap-2">
              <Button 
                onClick={() => triggerScan('keywords_gsc')} 
                variant="outline" 
                size="sm" 
                className="gap-2 border-indigo-500/20 hover:border-indigo-500/40"
              >
                <Globe size={14} />
                Sync from GSC
              </Button>
              <Button 
                onClick={() => triggerScan('seo')} 
                variant="outline" 
                size="sm" 
                className="gap-2 border-primary/20 hover:border-primary/40"
              >
                <RefreshCw size={14} className={keywordsLoading ? "animate-spin" : ""} />
                Refresh AI Keywords
              </Button>
            </div>
          </div>
          {keywordsLoading ? (
            <div className="space-y-4">
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-64 w-full" />
            </div>
          ) : (
            <KeywordTable keywords={filteredKeywords} onSearch={setSearch} />
          )}
        </TabsContent>

        <TabsContent value="rankings">
          <RankTracker projectId={activeProject.id} />
        </TabsContent>

        <TabsContent value="onpage">
          <OnPageScore projectId={activeProject.id} />
        </TabsContent>

        <TabsContent value="backlinks">
          <BacklinkDashboard projectId={activeProject.id} />
        </TabsContent>

        <TabsContent value="competitors">
          <CompetitorAnalysis projectId={activeProject.id} />
        </TabsContent>

        <TabsContent value="gaps" className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-lg font-semibold text-text-primary">Content Gaps</h2>
              <p className="text-sm text-text-muted">Topics your competitors rank for but you don&apos;t</p>
            </div>
            <Button 
              onClick={() => triggerScan('gaps')} 
              variant="outline" 
              size="sm" 
              className="gap-2 border-indigo-500/20 hover:border-indigo-500/40"
            >
              <FileSearch size={14} className={gapsLoading ? "animate-spin" : ""} />
              Find Gaps
            </Button>
          </div>
          {gapsLoading ? (
            <Skeleton className="h-64 w-full" />
          ) : (
            <ContentGaps gaps={gaps || []} />
          )}
        </TabsContent>

        <TabsContent value="technical" className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-lg font-semibold text-text-primary">Technical Audit</h2>
              <p className="text-sm text-text-muted">Core technical health checks for your domain</p>
            </div>
            <Button 
              onClick={() => triggerScan('technical')} 
              variant="outline" 
              size="sm" 
              className="gap-2 border-success/20 hover:border-success/40"
            >
              <ShieldCheck size={14} className={technicalLoading ? "animate-spin" : ""} />
              Run Technical Audit
            </Button>
          </div>
          {technicalLoading ? (
            <Skeleton className="h-64 w-full" />
          ) : (
            <TechnicalSEO checks={technicalChecks || []} />
          )}
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
