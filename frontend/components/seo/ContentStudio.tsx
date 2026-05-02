"use client";
import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import {
  FileText, Sparkles, Layers, Edit3, RefreshCw,
} from "lucide-react";
import {
  useBriefs, useCreateBrief, useOptimizeContent, useClusters, useBuildCluster,
} from "@/hooks/useSEO";

export function ContentStudio({ projectId }: { projectId: string }) {
  return (
    <Tabs defaultValue="briefs" className="space-y-4">
      <TabsList>
        <TabsTrigger value="briefs">Content Briefs</TabsTrigger>
        <TabsTrigger value="optimizer">Optimizer</TabsTrigger>
        <TabsTrigger value="clusters">Topic Clusters</TabsTrigger>
      </TabsList>

      <TabsContent value="briefs"><BriefsTab projectId={projectId}/></TabsContent>
      <TabsContent value="optimizer"><OptimizerTab projectId={projectId}/></TabsContent>
      <TabsContent value="clusters"><ClustersTab projectId={projectId}/></TabsContent>
    </Tabs>
  );
}

function BriefsTab({ projectId }: { projectId: string }) {
  const [keyword, setKeyword] = useState("");
  const [target, setTarget] = useState(1500);
  const { data: briefs, isLoading } = useBriefs(projectId);
  const create = useCreateBrief();

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><FileText size={18}/> Generate Content Brief</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3">
            <Input placeholder="Target keyword" value={keyword} onChange={(e) => setKeyword(e.target.value)} className="flex-1"/>
            <Input type="number" value={target} onChange={(e) => setTarget(Number(e.target.value) || 1500)} className="w-32" placeholder="Words"/>
            <Button onClick={() => keyword && create.mutate({ projectId, payload: { target_keyword: keyword, target_word_count: target } })} disabled={!keyword || create.isPending} className="gap-2">
              {create.isPending ? <RefreshCw size={16} className="animate-spin"/> : <Sparkles size={16}/>}
              Generate
            </Button>
          </div>
        </CardContent>
      </Card>

      {isLoading ? <Skeleton className="h-32"/> : briefs?.length ? (
        <div className="space-y-4">
          {briefs.map((b: any) => (
            <Card key={b.id}>
              <CardHeader>
                <CardTitle className="text-base">{b.target_keyword}</CardTitle>
                <p className="text-xs text-text-muted">Target: {b.target_word_count.toLocaleString()} words • Avg competitors: {b.avg_competitor_words.toLocaleString()}</p>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="font-medium mb-2">Title suggestions</p>
                    <ul className="space-y-1 text-text-muted">
                      {b.title_suggestions?.map((t: string, i: number) => <li key={i}>• {t}</li>)}
                    </ul>
                  </div>
                  <div>
                    <p className="font-medium mb-2">Outline</p>
                    <ul className="space-y-1 text-text-muted">
                      {b.outline?.slice(0, 6).map((h: string, i: number) => <li key={i}>{h}</li>)}
                    </ul>
                  </div>
                  <div>
                    <p className="font-medium mb-2">Semantic terms</p>
                    <div className="flex flex-wrap gap-1">
                      {b.semantic_terms?.slice(0, 15).map((t: string) => <Badge key={t} className="bg-card-hover text-text-muted border-0">{t}</Badge>)}
                    </div>
                  </div>
                  <div>
                    <p className="font-medium mb-2">Questions to answer</p>
                    <ul className="space-y-1 text-text-muted">
                      {b.questions_to_answer?.slice(0, 5).map((q: string, i: number) => <li key={i}>• {q}</li>)}
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : <p className="text-sm text-text-muted text-center py-8">No briefs yet. Generate one to see SERP-driven recommendations.</p>}
    </div>
  );
}

function OptimizerTab({ projectId }: { projectId: string }) {
  const [keyword, setKeyword] = useState("");
  const [content, setContent] = useState("");
  const optimize = useOptimizeContent();
  const data = optimize.data;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Edit3 size={18}/> Content Optimizer</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Input placeholder="Target keyword" value={keyword} onChange={(e) => setKeyword(e.target.value)}/>
          <textarea
            placeholder="Paste your draft (HTML or text)"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            className="w-full min-h-[200px] p-3 rounded border bg-card text-sm font-mono"
          />
          <Button
            onClick={() => keyword && content && optimize.mutate({ projectId, payload: { target_keyword: keyword, content } })}
            disabled={!keyword || !content || optimize.isPending}
            className="gap-2"
          >
            {optimize.isPending ? <RefreshCw size={16} className="animate-spin"/> : <Sparkles size={16}/>}
            Score
          </Button>
        </CardContent>
      </Card>

      {data && (
        <Card>
          <CardHeader><CardTitle>Result</CardTitle></CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4">
              <Stat label="Overall" value={data.overall_score}/>
              <Stat label="Headings" value={data.headings_score}/>
              <Stat label="Words" value={data.word_count}/>
              <Stat label="Density" value={`${data.keyword_density}%`}/>
              <Stat label="Readability" value={`${data.readability_score} (${data.grade_level})`}/>
            </div>
            <div className="mb-3">
              <p className="text-xs text-text-muted mb-1">Semantic coverage</p>
              <Progress value={Math.round(data.semantic_coverage * 100)} className="h-2"/>
            </div>
            <p className="font-medium mb-2 text-sm">Suggestions</p>
            <ul className="space-y-1 text-sm text-text-muted">
              {data.suggestions?.map((s: any, i: number) => (
                <li key={i}><Badge className="bg-amber-500/10 text-amber-700 border-amber-500/30 mr-2">{s.type}</Badge>{s.text}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function ClustersTab({ projectId }: { projectId: string }) {
  const [pillar, setPillar] = useState("");
  const { data: clustersResponse, isLoading } = useClusters(projectId);
  const clusters = clustersResponse?.data || [];
  const build = useBuildCluster();

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Layers size={18}/> Topic Clusters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3">
            <Input placeholder="Pillar topic (e.g. 'email marketing')" value={pillar} onChange={(e) => setPillar(e.target.value)} className="flex-1"/>
            <Button onClick={() => pillar && build.mutate({ projectId, pillar })} disabled={!pillar || build.isPending} className="gap-2">
              {build.isPending ? <RefreshCw size={16} className="animate-spin"/> : <Layers size={16}/>}
              Build Cluster
            </Button>
          </div>
        </CardContent>
      </Card>

      {isLoading ? <Skeleton className="h-32"/> : clusters?.length ? (
        <div className="space-y-3">
          {clusters.map((c: any) => (
            <Card key={c.id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">{c.pillar_topic}</CardTitle>
                  <Badge className="bg-emerald-500/10 text-emerald-700 border-emerald-500/30">
                    Coverage {c.coverage_score}/100
                  </Badge>
                </div>
                <p className="text-xs text-text-muted">{c.supporting_topics?.length ?? 0} supporting articles • Total volume: {c.total_volume.toLocaleString()}</p>
              </CardHeader>
              <CardContent>
                <div className="space-y-1">
                  {c.supporting_topics?.map((t: any, i: number) => (
                    <div key={i} className="flex items-center justify-between p-2 rounded hover:bg-card-hover text-sm">
                      <span>{t.topic}</span>
                      <div className="flex items-center gap-3 text-xs text-text-muted">
                        <span>vol {t.monthly_volume?.toLocaleString()}</span>
                        <span>KD {t.difficulty}</span>
                        <Badge className="bg-card-hover text-text-muted border-0 text-[10px]">{t.intent}</Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : <p className="text-sm text-text-muted text-center py-8">No clusters yet. Build one from a pillar topic.</p>}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: any }) {
  return (
    <div className="p-3 rounded border">
      <p className="text-xs uppercase tracking-wider text-text-muted">{label}</p>
      <p className="text-lg font-bold mt-1">{value}</p>
    </div>
  );
}
