"use client";
import React, { useState } from "react";
import { 
  Bot, Sparkles, MessageSquare, ListTree, 
  Lightbulb, TrendingUp, Search, ChevronRight, Zap
} from "lucide-react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { ScanModal } from "@/components/layout/ScanModal";
import { 
  AEODashboard, 
  AIVisibilityTracker, 
  SnippetTracker, 
  ContentRecommendations, 
  FAQGenerator 
} from "@/components/aeo";
import { useActiveProject } from "@/hooks/useProject";

export default function AEOPage() {
  const { activeProject } = useActiveProject();
  const [tab, setTab] = useState("dashboard");
  const [isScanModalOpen, setIsScanModalOpen] = useState(false);

  if (!activeProject) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <p className="text-text-muted">Please select a project to view AEO data.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2">
            AEO Hub <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-primary/20 text-primary uppercase">Beta</span>
          </h1>
          <p className="text-text-muted text-sm mt-1">
            Answer Engine Optimization: Track visibility in LLMs, featured snippets, and AI-powered search.
          </p>
        </div>
        <button
          onClick={() => setIsScanModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-semibold rounded-lg transition-all"
        >
          <Zap size={16} />
          <span>Run AI Scan</span>
        </button>
      </div>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList>
          <TabsTrigger value="dashboard" className="gap-2">
            <TrendingUp className="w-4 h-4" /> Overview
          </TabsTrigger>
          <TabsTrigger value="visibility" className="gap-2">
            <Bot className="w-4 h-4" /> LLM Visibility
          </TabsTrigger>
          <TabsTrigger value="snippets" className="gap-2">
            <Sparkles className="w-4 h-4" /> Snippets & PAA
          </TabsTrigger>
          <TabsTrigger value="recommendations" className="gap-2">
            <Lightbulb className="w-4 h-4" /> Content Strategy
          </TabsTrigger>
          <TabsTrigger value="faqs" className="gap-2">
            <MessageSquare className="w-4 h-4" /> AI FAQs
          </TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard">
          <AEODashboard projectId={activeProject.id} />
        </TabsContent>

        <TabsContent value="visibility">
          <AIVisibilityTracker projectId={activeProject.id} />
        </TabsContent>

        <TabsContent value="snippets">
          <SnippetTracker projectId={activeProject.id} />
        </TabsContent>

        <TabsContent value="recommendations">
          <ContentRecommendations projectId={activeProject.id} />
        </TabsContent>

        <TabsContent value="faqs">
          <FAQGenerator projectId={activeProject.id} />
        </TabsContent>
      </Tabs>

      <ScanModal
        isOpen={isScanModalOpen}
        onClose={() => setIsScanModalOpen(false)}
        projectId={activeProject?.id}
        featureType="ai"
      />
    </div>
  );
}
