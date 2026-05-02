"use client";
import React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Globe, FileText, Link2, Sparkles, Activity, MapPin, Shield, AlertCircle,
  TrendingUp, BookOpen, Presentation, Zap, Bell, FileSearch
} from "lucide-react";
import { useSEOHubOverview } from "@/hooks/useSEO";

export function SEOHubOverview({ projectId }: { projectId: string }) {
  const { data, isLoading } = useSEOHubOverview(projectId);

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
        {[...Array(12)].map((_, i) => <Skeleton key={i} className="h-24"/>)}
      </div>
    );
  }
  if (!data) return null;

  const score = data.site_score ?? 0;
  const scoreColor = score >= 80 ? "text-emerald-600" : score >= 60 ? "text-amber-600" : "text-red-600";

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
      <Tile icon={Globe} label="Site Health" value={`${score}/100`} valueColor={scoreColor}/>
      <Tile icon={AlertCircle} label="Issues" value={data.total_issues} hint={`${data.errors} errors`}/>
      <Tile icon={Activity} label="Performance" value={data.core_web_vitals_score ?? "—"}/>
      <Tile icon={Sparkles} label="Tracked" value={data.keywords_tracked} hint="Keywords"/>
      <Tile icon={Link2} label="Backlinks" value={data.backlinks} hint={`${data.referring_domains} domains`}/>
      <Tile icon={Shield} label="Toxic" value={data.toxic_backlinks ?? 0} valueColor={(data.toxic_backlinks ?? 0) > 0 ? "text-red-600" : ""}/>
      <Tile icon={Presentation} label="Domain Rank" value={data.authority_score ?? "—"} hint="Avg Authority"/>
      <Tile icon={FileSearch} label="Content" value={data.content_briefs ?? 0} hint="AI Briefs"/>
      <Tile icon={Zap} label="Topic" value={data.clusters ?? 0} hint="Clusters"/>
      <Tile icon={Bell} label="Mentions" value={data.mentions ?? 0} hint="Brand Alerts"/>
      <Tile icon={MapPin} label="Local" value={data.citations ?? 0} hint="Citations"/>
      <Tile icon={TrendingUp} label="Visibility" value={data.share_of_voice ? `${data.share_of_voice}%` : "—"} hint="Market Share"/>
    </div>
  );
}

function Tile({ icon: Icon, label, value, hint, valueColor }: { icon: any; label: string; value: any; hint?: string; valueColor?: string }) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <p className="text-xs uppercase tracking-wider text-text-muted">{label}</p>
          <Icon size={16} className="text-text-muted"/>
        </div>
        <p className={`text-2xl font-bold mt-1 ${valueColor || ""}`}>{value}</p>
        {hint && <p className="text-xs text-text-muted mt-1">{hint}</p>}
      </CardContent>
    </Card>
  );
}
