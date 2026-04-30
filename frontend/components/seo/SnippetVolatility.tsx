"use client";
import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Star, TrendingUp, TrendingDown, RefreshCw } from "lucide-react";
import {
  useSnippetWatch, useCheckSnippet, usePAA, useVolatility,
} from "@/hooks/useSEO";

export function SnippetVolatility({ projectId }: { projectId: string }) {
  return (
    <Tabs defaultValue="snippets" className="space-y-4">
      <TabsList>
        <TabsTrigger value="snippets">Featured Snippets</TabsTrigger>
        <TabsTrigger value="paa">People Also Ask</TabsTrigger>
        <TabsTrigger value="volatility">SERP Volatility</TabsTrigger>
      </TabsList>
      <TabsContent value="snippets"><SnippetsTab projectId={projectId}/></TabsContent>
      <TabsContent value="paa"><PAATab projectId={projectId}/></TabsContent>
      <TabsContent value="volatility"><VolatilityTab projectId={projectId}/></TabsContent>
    </Tabs>
  );
}

function SnippetsTab({ projectId }: { projectId: string }) {
  const [keyword, setKeyword] = useState("");
  const { data: watch, isLoading } = useSnippetWatch(projectId);
  const check = useCheckSnippet();

  return (
    <div className="space-y-3">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Star size={18}/> Featured Snippet Watch</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Input placeholder="Keyword" value={keyword} onChange={(e) => setKeyword(e.target.value)}/>
            <Button onClick={() => keyword && check.mutate({ projectId, keyword })} disabled={!keyword || check.isPending} className="gap-2">
              {check.isPending ? <RefreshCw size={16} className="animate-spin"/> : <Star size={16}/>}
              Check
            </Button>
          </div>
        </CardContent>
      </Card>
      {isLoading ? <Skeleton className="h-32"/> : !watch?.length ? (
        <p className="text-sm text-text-muted text-center py-8">No snippets tracked yet.</p>
      ) : (
        <div className="space-y-2">
          {watch.map((w: any) => (
            <div key={w.id} className="p-3 rounded border">
              <div className="flex items-center justify-between gap-2">
                <p className="font-medium text-sm">{w.keyword}</p>
                {w.we_own
                  ? <Badge className="bg-emerald-500/10 text-emerald-700 border-emerald-500/30">You own it 🎉</Badge>
                  : <Badge className="bg-amber-500/10 text-amber-700 border-amber-500/30">Not yours</Badge>}
              </div>
              {w.current_owner_url && (
                <a href={w.current_owner_url} target="_blank" rel="noreferrer" className="text-xs text-blue-600 hover:underline">
                  {w.current_owner_url}
                </a>
              )}
              {w.snippet_text && <p className="text-xs text-text-muted mt-1 line-clamp-2">{w.snippet_text}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function PAATab({ projectId }: { projectId: string }) {
  const { data, isLoading } = usePAA(projectId);
  return (
    <Card>
      <CardHeader><CardTitle className="text-base">People Also Ask Questions</CardTitle></CardHeader>
      <CardContent>
        {isLoading ? <Skeleton className="h-32"/> : !data?.length ? (
          <p className="text-sm text-text-muted text-center py-4">No PAA questions tracked yet.</p>
        ) : (
          <div className="space-y-2">
            {data.map((q: any) => (
              <div key={q.id} className="p-3 rounded border">
                <p className="font-medium text-sm">{q.question}</p>
                <p className="text-xs text-text-muted">Seed: {q.seed_keyword}</p>
                {q.answer_snippet && <p className="text-xs mt-1 line-clamp-2">{q.answer_snippet}</p>}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function VolatilityTab({ projectId }: { projectId: string }) {
  const { data, isLoading } = useVolatility(projectId);
  return (
    <Card>
      <CardHeader><CardTitle className="text-base">Recent SERP Movement</CardTitle></CardHeader>
      <CardContent>
        {isLoading ? <Skeleton className="h-32"/> : !data?.length ? (
          <p className="text-sm text-text-muted text-center py-4">No volatility events yet.</p>
        ) : (
          <div className="space-y-2">
            {data.map((e: any) => (
              <div key={e.id} className="p-3 rounded border flex items-center justify-between gap-2">
                <div>
                  <p className="font-medium text-sm">{e.keyword}</p>
                  <p className="text-xs text-text-muted">
                    {e.previous_position ?? "—"} → {e.current_position ?? "—"}
                  </p>
                </div>
                <Badge className={e.direction === "up"
                  ? "bg-emerald-500/10 text-emerald-700 border-emerald-500/30"
                  : "bg-red-500/10 text-red-700 border-red-500/30"}>
                  {e.direction === "up"
                    ? <><TrendingUp size={12} className="inline mr-1"/> +{Math.abs(e.delta)}</>
                    : <><TrendingDown size={12} className="inline mr-1"/> -{Math.abs(e.delta)}</>}
                </Badge>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
