"use client";
import React, { useState } from "react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Zap } from "lucide-react";
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

export default function SEOPage() {
  const { activeProject } = useActiveProject();
  const [tab, setTab] = useState("keywords");
  const [search, setSearch] = useState("");
  const [isScanModalOpen, setIsScanModalOpen] = useState(false);

  // Fetch real data from backend
  const { data: keywordResponse, isLoading: keywordsLoading } = useKeywords(activeProject?.id || "", search);
  const { data: gapsResponse, isLoading: gapsLoading } = useContentGaps(activeProject?.id || "");
  const { data: technicalResponse, isLoading: technicalLoading } = useTechnicalChecks(activeProject?.id || "");

  // Extract data from paginated responses
  const keywords = (keywordResponse?.data || []) as any[];
  const gaps = (gapsResponse?.data || []) as any[];
  const technicalChecks = (technicalResponse?.data || []) as any[];

  const filteredKeywords = keywords.filter((k) =>
    search ? k.keyword?.toLowerCase().includes(search.toLowerCase()) : true
  );

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
        <button
          onClick={() => setIsScanModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-semibold rounded-lg transition-all"
        >
          <Zap size={16} />
          <span>Run SEO Scan</span>
        </button>
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

        <TabsContent value="keywords">
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

        <TabsContent value="gaps">
          <div className="space-y-4">
            <div>
              <h2 className="text-lg font-semibold text-text-primary">Content Gaps</h2>
              <p className="text-sm text-text-muted">Topics your competitors rank for but you don&apos;t</p>
            </div>
            {gapsLoading ? (
              <Skeleton className="h-64 w-full" />
            ) : (
              <ContentGaps gaps={gaps || []} />
            )}
          </div>
        </TabsContent>

        <TabsContent value="technical">
          <div className="space-y-4">
            <div>
              <h2 className="text-lg font-semibold text-text-primary">Technical Audit</h2>
              <p className="text-sm text-text-muted">Core technical health checks for your domain</p>
            </div>
            {technicalLoading ? (
              <Skeleton className="h-64 w-full" />
            ) : (
              <TechnicalSEO checks={technicalChecks || []} />
            )}
          </div>
        </TabsContent>
      </Tabs>

      <ScanModal
        isOpen={isScanModalOpen}
        onClose={() => setIsScanModalOpen(false)}
        projectId={activeProject?.id}
        featureType="seo"
      />
    </div>
  );
}

