'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { 
  Sparkles, ListChecks, Download, RefreshCw, 
  Search, AlertCircle, Info, Zap
} from 'lucide-react';
import { useBulkKeywordMetrics } from '@/hooks/useSEO';

export function BulkKeywordChecker({ projectId }: { projectId: string }) {
  const [keywordsText, setKeywordsText] = useState('');
  const bulk = useBulkKeywordMetrics();

  const handleRun = () => {
    const list = keywordsText.split('\n').map(k => k.trim()).filter(Boolean);
    if (list.length > 0) {
      bulk.mutate(list);
    }
  };

  const getIntentColor = (intent: string) => {
    switch (intent.toLowerCase()) {
      case 'informational': return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'transactional': return 'bg-emerald-100 text-emerald-700 border-emerald-200';
      case 'commercial': return 'bg-amber-100 text-amber-700 border-amber-200';
      case 'navigational': return 'bg-purple-100 text-purple-700 border-purple-200';
      default: return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  const getDifficultyColor = (score: number) => {
    if (score > 70) return 'text-red-600';
    if (score > 40) return 'text-amber-600';
    return 'text-emerald-600';
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-primary" />
            Bulk Keyword Checker
          </CardTitle>
          <CardDescription>
            Instantly get Search Volume and Difficulty metrics for up to 100 keywords.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <textarea
            placeholder="Enter keywords (one per line)..."
            value={keywordsText}
            onChange={(e) => setKeywordsText(e.target.value)}
            className="w-full min-h-[160px] p-4 rounded-lg border bg-background text-sm font-mono focus:ring-2 focus:ring-primary/20 outline-none transition-shadow"
          />
          <div className="flex items-center justify-between">
            <p className="text-xs text-muted-foreground flex items-center gap-1">
              <Info className="h-3 w-3" />
              {keywordsText.split('\n').filter(Boolean).length} / 100 keywords
            </p>
            <Button onClick={handleRun} disabled={bulk.isPending || !keywordsText.trim()} className="gap-2 px-6">
              {bulk.isPending ? <RefreshCw className="h-4 w-4 animate-spin" /> : <ListChecks className="h-4 w-4" />}
              Get Metrics
            </Button>
          </div>
        </CardContent>
      </Card>

      {bulk.isPending && (
        <div className="space-y-2">
          {[1, 2, 3, 4, 5].map(i => <Skeleton key={i} className="h-12 w-full" />)}
        </div>
      )}

      {bulk.data && (
        <Card className="animate-in fade-in slide-in-from-bottom-2 duration-500 overflow-hidden">
          <CardHeader className="bg-muted/30 border-b py-4">
            <div className="flex items-center justify-between">
               <CardTitle className="text-base font-semibold">Results ({bulk.data.results.length})</CardTitle>
               <Button variant="outline" size="sm" className="h-8 gap-2">
                 <Download className="h-3 w-3" />
                 Export CSV
               </Button>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-auto max-h-[600px]">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-muted/10 text-xs text-muted-foreground uppercase tracking-wider text-left border-b">
                    <th className="p-4 font-semibold">Keyword</th>
                    <th className="p-4 font-semibold text-right">Volume</th>
                    <th className="p-4 font-semibold text-right">KD %</th>
                    <th className="p-4 font-semibold text-right">CPC (USD)</th>
                    <th className="p-4 font-semibold text-center">Intent</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {bulk.data.results.map((res, i) => (
                    <tr key={i} className="hover:bg-muted/30 transition-colors">
                      <td className="p-4 font-medium">{res.keyword}</td>
                      <td className="p-4 text-right tabular-nums">{res.volume.toLocaleString()}</td>
                      <td className="p-4 text-right tabular-nums">
                        <span className={`font-bold ${getDifficultyColor(res.difficulty)}`}>
                          {res.difficulty}
                        </span>
                      </td>
                      <td className="p-4 text-right tabular-nums">${res.cpc_usd.toFixed(2)}</td>
                      <td className="p-4 text-center">
                        <Badge variant="outline" className={`text-[10px] uppercase font-bold border-none ${getIntentColor(res.intent)}`}>
                          {res.intent}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {bulk.data?.results.length === 0 && (
        <div className="py-12 text-center text-muted-foreground bg-slate-50 dark:bg-slate-900/50 rounded-lg border border-dashed">
          No metrics found. Try different keywords.
        </div>
      )}
    </div>
  );
}
