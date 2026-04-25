"use client";
import React, { useState } from "react";
import { 
  FolderPlus, 
  Search, 
  MoreHorizontal, 
  Trash2, 
  ChevronRight, 
  ChevronDown,
  LayoutGrid,
  List as ListIcon,
  CheckSquare,
  Square
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useKeywords, useClusters, useCreateCluster } from "@/hooks/useSEO";
import { cn } from "@/lib/utils";

interface KeywordManagerProps {
  projectId: string;
}

export function KeywordManager({ projectId }: KeywordManagerProps) {
  const { data: kwResponse, isLoading: kwLoading } = useKeywords(projectId);
  const { data: clusterResponse, isLoading: clusterLoading } = useClusters(projectId);
  const createCluster = useCreateCluster();
  
  const [selectedKws, setSelectedKeywords] = useState<string[]>([]);
  const [topicName, setTopicName] = useState("");
  const [search, setSearch] = useState("");

  const keywords = kwResponse?.data || [];
  const clusters = clusterResponse?.data || [];

  const unclustered = keywords.filter(kw => !kw.cluster_id);
  const filtered = unclustered.filter(kw => kw.keyword.toLowerCase().includes(search.toLowerCase()));

  const toggleSelect = (keyword: string) => {
    if (selectedKws.includes(keyword)) {
      setSelectedKeywords(selectedKws.filter(k => k !== keyword));
    } else {
      setSelectedKeywords([...selectedKws, keyword]);
    }
  };

  const handleCreateCluster = async () => {
    if (!topicName || selectedKws.length === 0) return;
    try {
      await createCluster.mutateAsync({
        projectId,
        data: {
          topic_name: topicName,
          keywords: selectedKws
        }
      });
      setTopicName("");
      setSelectedKeywords([]);
    } catch (err) {
      console.error(err);
    }
  };

  if (kwLoading || clusterLoading) return <Skeleton className="h-96 w-full" />;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Left: Unclustered Keywords */}
      <Card className="lg:col-span-2">
        <CardHeader className="pb-3 border-b border-border">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Unclustered Keywords</CardTitle>
            <Badge variant="secondary">{unclustered.length} remaining</Badge>
          </div>
          <div className="mt-4 flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-text-muted" />
              <Input 
                placeholder="Search keywords..." 
                className="pl-9"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            {selectedKws.length > 0 && (
              <div className="flex gap-2">
                <Input 
                  placeholder="Topic Name..." 
                  className="w-48"
                  value={topicName}
                  onChange={(e) => setTopicName(e.target.value)}
                />
                <Button onClick={handleCreateCluster} disabled={createCluster.isPending}>
                  <FolderPlus className="h-4 w-4 mr-2" />
                  Cluster ({selectedKws.length})
                </Button>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent className="p-0 max-h-[600px] overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-surface2 border-b border-border z-10">
              <tr className="text-left text-xs font-semibold text-text-muted uppercase tracking-wider">
                <th className="px-4 py-2 w-10">
                   <Button 
                    variant="ghost" size="sm" className="p-0 h-6 w-6"
                    onClick={() => {
                      if (selectedKws.length === filtered.length) setSelectedKeywords([]);
                      else setSelectedKeywords(filtered.map(k => k.keyword));
                    }}
                   >
                     {selectedKws.length === filtered.length ? <CheckSquare className="h-4 w-4" /> : <Square className="h-4 w-4" />}
                   </Button>
                </th>
                <th className="px-4 py-2">Keyword</th>
                <th className="px-4 py-2 text-right">Volume</th>
                <th className="px-4 py-2 text-right">Difficulty</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((kw) => (
                <tr 
                  key={kw.id} 
                  className={cn(
                    "border-b border-border hover:bg-surface2/50 cursor-pointer",
                    selectedKws.includes(kw.keyword) && "bg-primary/5"
                  )}
                  onClick={() => toggleSelect(kw.keyword)}
                >
                  <td className="px-4 py-3">
                    {selectedKws.includes(kw.keyword) ? (
                      <CheckSquare className="h-4 w-4 text-primary" />
                    ) : (
                      <Square className="h-4 w-4 text-text-muted" />
                    )}
                  </td>
                  <td className="px-4 py-3 font-medium">{kw.keyword}</td>
                  <td className="px-4 py-3 text-right text-text-muted">{kw.volume?.toLocaleString()}</td>
                  <td className="px-4 py-3 text-right">
                    <span className={cn(
                      "px-2 py-0.5 rounded text-[10px] font-bold",
                      kw.difficulty > 70 ? "bg-red-500/10 text-red-500" :
                      kw.difficulty > 30 ? "bg-orange-500/10 text-orange-500" :
                      "bg-green-500/10 text-green-500"
                    )}>
                      {kw.difficulty}
                    </span>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-4 py-10 text-center text-text-muted">
                    {search ? "No matches found" : "All keywords are clustered!"}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>

      {/* Right: Existing Clusters */}
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <LayoutGrid className="h-5 w-5 text-primary" />
              Active Clusters
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {clusters.map((cluster: any) => (
              <div 
                key={cluster.id}
                className="p-4 rounded-xl border border-border bg-surface2/30 hover:border-primary/30 transition-all group"
              >
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-semibold text-text-primary group-hover:text-primary transition-colors">
                    {cluster.topic_name}
                  </h4>
                  <Badge variant="outline" className="text-[10px]">
                    {cluster.keywords?.length || 0} keywords
                  </Badge>
                </div>
                <div className="flex flex-wrap gap-1">
                  {(cluster.keywords || []).slice(0, 5).map((k: string) => (
                    <span key={k} className="text-[10px] bg-background px-1.5 py-0.5 rounded border border-border text-text-muted">
                      {k}
                    </span>
                  ))}
                  {cluster.keywords?.length > 5 && (
                    <span className="text-[10px] text-text-tertiary">+{cluster.keywords.length - 5} more</span>
                  )}
                </div>
              </div>
            ))}
            {clusters.length === 0 && (
              <div className="text-center py-10 text-text-muted italic">
                No clusters created yet.
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
