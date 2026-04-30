"use client";
import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Network, RefreshCw, Ghost } from "lucide-react";
import {
  useInternalLinks, useOrphanPages, useAnalyzeInternalLinks,
} from "@/hooks/useSEO";

export function InternalLinksAnalyzer({ projectId }: { projectId: string }) {
  const [textareaValue, setTextareaValue] = useState("");
  const { data: links, isLoading: linksLoading } = useInternalLinks(projectId);
  const { data: orphans, isLoading: orphansLoading } = useOrphanPages(projectId);
  const analyze = useAnalyzeInternalLinks();

  const run = () => {
    const urls = textareaValue.split(/[\s,]+/).filter((u) => u.startsWith("http"));
    if (urls.length === 0) return;
    analyze.mutate({ projectId, urls });
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Network size={18}/> Internal Link Analyzer</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <textarea
            placeholder={"Paste URLs (one per line) — these will be crawled for internal links\nhttps://example.com/page-1\nhttps://example.com/page-2"}
            value={textareaValue}
            onChange={(e) => setTextareaValue(e.target.value)}
            className="w-full min-h-[120px] p-3 rounded border bg-card text-sm font-mono"
          />
          <Button onClick={run} disabled={analyze.isPending} className="gap-2">
            {analyze.isPending ? <RefreshCw size={16} className="animate-spin"/> : <Network size={16}/>}
            Analyze
          </Button>
          {analyze.data && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
              <Badge className="bg-card-hover">Edges: {analyze.data.edges}</Badge>
              <Badge className="bg-card-hover">Nodes: {analyze.data.nodes}</Badge>
              <Badge className="bg-amber-500/10 text-amber-700 border-amber-500/30">Orphans: {analyze.data.orphans}</Badge>
              <Badge className="bg-amber-500/10 text-amber-700 border-amber-500/30">Dead-ends: {analyze.data.dead_ends}</Badge>
            </div>
          )}
        </CardContent>
      </Card>

      <Tabs defaultValue="links">
        <TabsList>
          <TabsTrigger value="links">Internal Links</TabsTrigger>
          <TabsTrigger value="orphans">Orphan Pages</TabsTrigger>
        </TabsList>
        <TabsContent value="links">
          <Card>
            <CardContent className="p-0">
              {linksLoading ? <Skeleton className="h-32 m-4"/> : !links?.length ? (
                <p className="text-sm text-text-muted text-center py-8">No internal links analyzed yet.</p>
              ) : (
                <div className="overflow-auto max-h-[500px]">
                  <table className="w-full text-sm">
                    <thead className="text-xs text-text-muted sticky top-0 bg-card">
                      <tr>
                        <th className="text-left p-2">From</th>
                        <th className="text-left p-2">To</th>
                        <th className="text-left p-2">Anchor</th>
                        <th className="text-left p-2">Position</th>
                        <th className="text-left p-2">Follow</th>
                      </tr>
                    </thead>
                    <tbody>
                      {links.slice(0, 200).map((l: any) => (
                        <tr key={l.id} className="border-t">
                          <td className="p-2 truncate max-w-xs">{l.source_url}</td>
                          <td className="p-2 truncate max-w-xs">{l.target_url}</td>
                          <td className="p-2 truncate max-w-xs">{l.anchor_text}</td>
                          <td className="p-2"><Badge className="bg-card-hover text-text-muted border-0 text-[10px]">{l.link_position}</Badge></td>
                          <td className="p-2">
                            {l.is_nofollow
                              ? <Badge className="bg-amber-500/10 text-amber-700 border-amber-500/30">nofollow</Badge>
                              : <Badge className="bg-emerald-500/10 text-emerald-700 border-emerald-500/30">follow</Badge>}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="orphans">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Ghost size={16}/> Orphan Pages — no internal links pointing to them
              </CardTitle>
            </CardHeader>
            <CardContent>
              {orphansLoading ? <Skeleton className="h-32"/> : !orphans?.length ? (
                <p className="text-sm text-text-muted text-center py-8">No orphan pages detected.</p>
              ) : (
                <div className="space-y-1">
                  {orphans.map((o: any) => (
                    <div key={o.id} className="p-2 rounded border flex items-center justify-between text-sm">
                      <a href={o.url} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline truncate">{o.url}</a>
                      <Badge className="bg-card-hover">PA {o.page_authority.toFixed(0)}</Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
