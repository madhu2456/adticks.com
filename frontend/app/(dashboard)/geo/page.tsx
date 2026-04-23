"use client";
import React, { useState } from "react";
import { 
  MapPin, Star, Search, Globe, 
  CheckCircle2, AlertTriangle, TrendingUp,
  Map as MapIcon, MessageSquare, ClipboardCheck
} from "lucide-react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { LocationList } from "@/components/geo/LocationList";
import { LocalRankCards } from "@/components/geo/LocalRankCards";
import { ReviewDashboard } from "@/components/geo/ReviewDashboard";
import { CitationAudit } from "@/components/geo/CitationAudit";
import { useActiveProject } from "@/hooks/useProject";

export default function GeoPage() {
  const { activeProject } = useActiveProject();
  const [tab, setTab] = useState("locations");

  if (!activeProject) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <p className="text-text-muted">Please select a project to view Local SEO data.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-text-primary">Local SEO & Geo</h1>
        <p className="text-text-muted text-sm mt-1">
          Manage physical locations, track Google Maps rankings, and monitor local reputation.
        </p>
      </div>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList>
          <TabsTrigger value="locations" className="gap-2">
            <MapPin className="w-4 h-4" /> Locations
          </TabsTrigger>
          <TabsTrigger value="rankings" className="gap-2">
            <MapIcon className="w-4 h-4" /> Local Rankings
          </TabsTrigger>
          <TabsTrigger value="reviews" className="gap-2">
            <MessageSquare className="w-4 h-4" /> Reviews
          </TabsTrigger>
          <TabsTrigger value="citations" className="gap-2">
            <ClipboardCheck className="w-4 h-4" /> Citations & NAP
          </TabsTrigger>
        </TabsList>

        <TabsContent value="locations">
          <LocationList projectId={activeProject.id} />
        </TabsContent>

        <TabsContent value="rankings">
          <div className="space-y-6">
             <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-surface-1 border border-white/5 p-4 rounded-2xl">
                   <p className="text-xs text-text-muted uppercase font-bold tracking-wider mb-1">Avg. Maps Rank</p>
                   <p className="text-2xl font-bold">#3.2</p>
                </div>
                <div className="bg-surface-1 border border-white/5 p-4 rounded-2xl">
                   <p className="text-xs text-text-muted uppercase font-bold tracking-wider mb-1">Top 3 Presence</p>
                   <p className="text-2xl font-bold text-success">68%</p>
                </div>
                <div className="bg-surface-1 border border-white/5 p-4 rounded-2xl">
                   <p className="text-xs text-text-muted uppercase font-bold tracking-wider mb-1">Local Actions</p>
                   <p className="text-2xl font-bold">+12%</p>
                </div>
             </div>
             <LocalRankCards projectId={activeProject.id} />
          </div>
        </TabsContent>

        <TabsContent value="reviews">
          <ReviewDashboard projectId={activeProject.id} />
        </TabsContent>

        <TabsContent value="citations">
          <CitationAudit projectId={activeProject.id} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
