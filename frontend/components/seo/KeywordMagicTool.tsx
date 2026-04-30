"use client";
import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Sparkles, Search, RefreshCw } from "lucide-react";
import { useKeywordIdeas, useKeywordMagic } from "@/hooks/useSEO";

const MATCH_TABS = ["all", "broad", "phrase", "exact", "related", "question"];

const intentColor: Record<string, string> = {
  informational: "bg-blue-500/10 text-blue-700 border-blue-500/30",
  commercial: "bg-violet-500/10 text-violet-700 border-violet-500/30",
  transactional: "bg-emerald-500/10 text-emerald-700 border-emerald-500/30",
  navigational: "bg-slate-500/10 text-slate-700 border-slate-500/30",
};

export function KeywordMagicTool({ projectId }: { projectId: string }) {
  const [seed, setSeed] = useState("");
  const [matchType, setMatchType] = useState("all");
  const { data: ideas, isLoading } = useKeywordIdeas(projectId, undefined, matchType === "all" ? undefined : matchType);
  const magic = useKeywordMagic();

  const generate = async () => {
    if (!seed) return;
    await magic.mutateAsync({
      projectId,
      payload: { seed, location: "us", include_questions: true, limit: 80 },
    });
  };

  const totalVolume = ideas?.reduce((s: number, i: any) => s + (i.volume || 0), 0) ?? 0;
  const avgKD = ideas?.length ? Math.round(ideas.reduce((s: number, i: any) => s + (i.difficulty || 0), 0) / ideas.length) : 0;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Sparkles size={18}/> Keyword Magic Tool</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3">
            <Input
              placeholder="Enter a seed keyword (e.g. 'email marketing')"
              value={seed}
              onChange={(e) => setSeed(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && generate()}
              className="flex-1"
            />
            <Button onClick={generate} disabled={!seed || magic.isPending} className="gap-2">
              {magic.isPending ? <RefreshCw size={16} className="animate-spin"/> : <Search size={16}/>}
              Generate Ideas
            </Button>
          </div>
        </CardContent>
      </Card>

      {(ideas?.length ?? 0) > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <StatCard label="Ideas" value={ideas!.length}/>
          <StatCard label="Total Volume" value={totalVolume.toLocaleString()}/>
          <StatCard label="Avg Difficulty" value={avgKD}/>
          <StatCard label="Questions" value={ideas!.filter((i: any) => i.match_type === "question").length}/>
        </div>
      )}

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Keyword Ideas</CardTitle>
          <div className="flex gap-1">
            {MATCH_TABS.map((tab) => (
              <button
                key={tab}
                onClick={() => setMatchType(tab)}
                className={`text-xs px-2.5 py-1 rounded ${matchType === tab ? "bg-primary text-white" : "bg-card-hover text-text-muted"}`}
              >
                {tab}
              </button>
            ))}
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">{[...Array(8)].map((_, i) => <Skeleton key={i} className="h-10"/>)}</div>
          ) : !ideas?.length ? (
            <p className="text-sm text-text-muted text-center py-8">Generate ideas from a seed keyword above.</p>
          ) : (
            <div className="overflow-auto max-h-[600px]">
              <table className="w-full text-sm">
                <thead className="text-xs text-text-muted sticky top-0 bg-card">
                  <tr>
                    <th className="text-left p-2">Keyword</th>
                    <th className="text-left p-2">Match</th>
                    <th className="text-left p-2">Intent</th>
                    <th className="text-right p-2">Volume</th>
                    <th className="text-right p-2">KD</th>
                    <th className="text-right p-2">CPC</th>
                    <th className="text-left p-2">SERP Features</th>
                  </tr>
                </thead>
                <tbody>
                  {ideas.map((kw: any) => (
                    <tr key={kw.id} className="border-t hover:bg-card-hover">
                      <td className="p-2 font-medium">{kw.keyword}</td>
                      <td className="p-2"><Badge className="bg-card-hover text-text-muted border-0 text-[10px]">{kw.match_type}</Badge></td>
                      <td className="p-2"><Badge className={`${intentColor[kw.intent]} text-[10px]`}>{kw.intent}</Badge></td>
                      <td className="p-2 text-right tabular-nums">{kw.volume.toLocaleString()}</td>
                      <td className="p-2 text-right tabular-nums">
                        <span className={kw.difficulty > 70 ? "text-red-600" : kw.difficulty > 40 ? "text-amber-600" : "text-emerald-600"}>
                          {kw.difficulty}
                        </span>
                      </td>
                      <td className="p-2 text-right tabular-nums">${kw.cpc.toFixed(2)}</td>
                      <td className="p-2 text-xs text-text-muted">{kw.serp_features?.slice(0, 2).join(", ")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number | string }) {
  return (
    <Card>
      <CardContent className="p-4">
        <p className="text-xs uppercase tracking-wider text-text-muted">{label}</p>
        <p className="text-2xl font-bold mt-1">{value}</p>
      </CardContent>
    </Card>
  );
}
