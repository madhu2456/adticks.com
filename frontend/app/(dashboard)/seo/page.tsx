"use client";
import React, { useState } from "react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { KeywordTable } from "@/components/seo/KeywordTable";
import { RankTracker } from "@/components/seo/RankTracker";
import { OnPageScore } from "@/components/seo/OnPageScore";
import { ContentGaps } from "@/components/seo/ContentGaps";
import { TechnicalSEO } from "@/components/seo/TechnicalSEO";
export default function SEOPage() {
  const [tab, setTab] = useState("keywords");
  const [search, setSearch] = useState("");

  const filteredKeywords = mockKeywords.filter((k) =>
    search ? k.keyword.toLowerCase().includes(search.toLowerCase()) : true
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-text-primary">SEO Hub</h1>
        <p className="text-text-muted text-sm mt-1">Track rankings, audit pages, and discover content opportunities</p>
      </div>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList>
          <TabsTrigger value="keywords">Keywords</TabsTrigger>
          <TabsTrigger value="rankings">Rankings</TabsTrigger>
          <TabsTrigger value="onpage">On-Page</TabsTrigger>
          <TabsTrigger value="gaps">Content Gaps</TabsTrigger>
          <TabsTrigger value="technical">Technical</TabsTrigger>
        </TabsList>

        <TabsContent value="keywords">
          <KeywordTable keywords={filteredKeywords} onSearch={setSearch} />
        </TabsContent>

        <TabsContent value="rankings">
          <RankTracker />
        </TabsContent>

        <TabsContent value="onpage">
          <OnPageScore />
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

