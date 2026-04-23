"use client";
import React, { useState } from "react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { KeywordTable } from "@/components/seo/KeywordTable";
import { RankTracker } from "@/components/seo/RankTracker";
import { OnPageScore } from "@/components/seo/OnPageScore";
import { ContentGaps } from "@/components/seo/ContentGaps";
import { TechnicalSEO } from "@/components/seo/TechnicalSEO";
import { BacklinkDashboard } from "@/components/seo/BacklinkDashboard";
import { CompetitorAnalysis } from "@/components/seo/CompetitorAnalysis";
import { mockKeywords, mockContentGaps, mockTechnicalChecks } from "@/lib/mockData";
import { useActiveProject } from "@/hooks/useProject";

export default function SEOPage() {
  const { activeProject } = useActiveProject();
  const [tab, setTab] = useState("keywords");
  const [search, setSearch] = useState("");

  const filteredKeywords = mockKeywords.filter((k) =>
    search ? k.keyword.toLowerCase().includes(search.toLowerCase()) : true
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
      <div>
        <h1 className="text-2xl font-bold text-text-primary">SEO Hub</h1>
        <p className="text-text-muted text-sm mt-1">Track rankings, audit pages, and discover content opportunities</p>
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
          <KeywordTable keywords={filteredKeywords} onSearch={setSearch} />
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
            <ContentGaps gaps={mockContentGaps} />
          </div>
        </TabsContent>

        <TabsContent value="technical">
          <div className="space-y-4">
            <div>
              <h2 className="text-lg font-semibold text-text-primary">Technical SEO</h2>
              <p className="text-sm text-text-muted">Core technical health checks for adticks.io</p>
            </div>
            <TechnicalSEO checks={mockTechnicalChecks} />
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

