'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { 
  Network, Sparkles, Plus, Trash2, Edit3, 
  ChevronRight, Layers, LayoutGrid, ListTree, RefreshCw
} from 'lucide-react';
import { useClusters, useBuildCluster, useDeleteCluster } from '@/hooks/useSEO';

export function TopicClusters({ projectId }: { projectId: string }) {
  const [pillar, setPillar] = useState('');
  const { data: clusters, isLoading } = useClusters(projectId);
  const build = useBuildCluster();
  const remove = useDeleteCluster();

  const handleBuild = () => {
    if (pillar) {
      build.mutate({ projectId, pillar });
      setPillar('');
    }
  };

  return (
    <div className="space-y-6">
      <Card className="border-indigo-100 bg-indigo-50/30 dark:bg-indigo-950/10">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Network className="h-5 w-5 text-indigo-600" />
            Topic Clusters
          </CardTitle>
          <CardDescription>
            Group keywords semantically around a pillar page to build topical authority.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Sparkles className="absolute left-2.5 top-2.5 h-4 w-4 text-indigo-400" />
              <input
                placeholder="Pillar Topic (e.g. 'Coffee Brewing')"
                className="w-full pl-8 pr-4 py-2 rounded-md border border-indigo-200 bg-background text-sm outline-none focus:ring-2 focus:ring-indigo-500/20"
                value={pillar}
                onChange={(e) => setPillar(e.target.value)}
              />
            </div>
            <Button onClick={handleBuild} disabled={build.isPending || !pillar} className="bg-indigo-600 hover:bg-indigo-700 gap-2">
              {build.isPending ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
              Build Cluster
            </Button>
          </div>
        </CardContent>
      </Card>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-48 w-full" />)}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {clusters?.data.map((cluster: any) => (
            <Card key={cluster.id} className="group hover:border-indigo-300 transition-all hover:shadow-md">
              <CardHeader className="pb-3 border-b bg-muted/20">
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <CardTitle className="text-base font-bold">{cluster.topic_name}</CardTitle>
                    <div className="flex items-center gap-1 text-[10px] text-muted-foreground uppercase font-semibold">
                      <Layers className="h-3 w-3" />
                      Pillar Topic
                    </div>
                  </div>
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    className="h-8 w-8 text-muted-foreground hover:text-red-600"
                    onClick={() => remove.mutate({ projectId, clusterId: cluster.id })}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="pt-4 space-y-4">
                <div className="flex flex-wrap gap-1.5">
                  {cluster.keywords.map((kw: string, i: number) => (
                    <Badge key={i} variant="secondary" className="bg-white dark:bg-slate-800 text-[10px] px-2 py-0 border-slate-100 shadow-sm">
                      {kw}
                    </Badge>
                  ))}
                  {cluster.keywords.length > 8 && (
                    <Badge variant="outline" className="text-[10px] border-none">+ {cluster.keywords.length - 8} more</Badge>
                  )}
                </div>

                <div className="pt-2 flex items-center justify-between">
                   <div className="flex -space-x-2">
                      {[1, 2, 3].map(i => (
                        <div key={i} className="w-6 h-6 rounded-full border-2 border-white bg-slate-200 flex items-center justify-center text-[8px] font-bold text-slate-500">
                          P{i}
                        </div>
                      ))}
                   </div>
                   <Button variant="ghost" size="sm" className="h-8 text-xs text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50 gap-1 pr-1">
                     Manage Cluster
                     <ChevronRight className="h-3 w-3" />
                   </Button>
                </div>
              </CardContent>
            </Card>
          ))}

          {clusters?.data.length === 0 && (
            <div className="col-span-full py-20 text-center border-2 border-dashed rounded-xl">
               <div className="bg-slate-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                  <ListTree className="h-8 w-8 text-slate-300" />
               </div>
               <h3 className="font-semibold text-slate-600">No clusters built yet</h3>
               <p className="text-sm text-slate-400 mt-1">Start by entering a pillar topic above.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
