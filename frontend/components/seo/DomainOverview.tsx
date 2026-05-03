'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { 
  Search, Shield, Users, Sparkles, Link2, 
  Target, Presentation, ArrowRight, ExternalLink 
} from 'lucide-react';
import { useDomainOverview } from '@/hooks/useSEO';

export function DomainOverview({ projectId }: { projectId: string }) {
  const [domain, setDomain] = useState('');
  const [searchDomain, setSearchDomain] = useState<string | null>(null);
  
  // If searching own domain, pass projectId for real data
  const isOwnDomain = searchDomain === projectId; // You'd need to get actual project domain
  const { data: overview, isLoading, isError } = useDomainOverview(
    searchDomain, 
    isOwnDomain ? projectId : undefined
  );

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (domain) {
      setSearchDomain(domain);
    }
  };

  return (
    <div className="space-y-6">
      <Card className="border-primary/20 bg-primary/5 shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Presentation className="h-5 w-5 text-primary" />
            Site Explorer
          </CardTitle>
          <CardDescription>
            Get a high-level 360° view of any domain's organic and paid performance.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearch} className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Enter domain (e.g. competitor.com)"
                className="pl-8 bg-background border-primary/20"
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
              />
            </div>
            <Button type="submit" disabled={isLoading} className="px-8 shadow-md">
              Search
            </Button>
          </form>
        </CardContent>
      </Card>

      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-28 w-full" />)}
        </div>
      )}

      {isError && (
        <Card className="border-destructive/50 bg-destructive/10">
          <CardContent className="py-6 text-center text-destructive">
            Failed to fetch domain overview.
          </CardContent>
        </Card>
      )}

      {!overview && !isLoading && !isError && (
        <div className="py-20 flex flex-col items-center justify-center text-center space-y-6 animate-in fade-in zoom-in">
          <div className="bg-primary/5 p-6 rounded-full ring-8 ring-primary/5">
            <Presentation className="h-12 w-12 text-primary opacity-80" />
          </div>
          <div className="max-w-md space-y-2">
            <h3 className="text-xl font-bold text-slate-800 dark:text-slate-200">Domain Intelligence</h3>
            <p className="text-muted-foreground text-sm leading-relaxed">
              Analyze your competitors' strengths. See their authority score, 
              estimated organic traffic, and backlink profile in seconds.
            </p>
          </div>
          <div className="flex flex-wrap justify-center gap-2 pt-4">
             <span className="text-xs text-muted-foreground w-full mb-1">Try these:</span>
            <Badge variant="secondary" className="px-3 py-1 cursor-pointer hover:bg-primary/10 transition-colors" onClick={() => { setDomain('amazon.com'); setSearchDomain('amazon.com'); }}>amazon.com</Badge>
            <Badge variant="secondary" className="px-3 py-1 cursor-pointer hover:bg-primary/10 transition-colors" onClick={() => { setDomain('wikipedia.org'); setSearchDomain('amazon.com'); }}>wikipedia.org</Badge>
            <Badge variant="secondary" className="px-3 py-1 cursor-pointer hover:bg-primary/10 transition-colors" onClick={() => { setDomain('hubspot.com'); setSearchDomain('hubspot.com'); }}>hubspot.com</Badge>
          </div>
        </div>
      )}

      {overview && (
        <div className="space-y-6 animate-in fade-in duration-500">
          {/* Top Level Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="bg-gradient-to-br from-indigo-50 to-transparent dark:from-indigo-950/20 border-indigo-100 dark:border-indigo-900">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between pb-2">
                  <p className="text-sm font-medium text-indigo-600 dark:text-indigo-400">Authority Score</p>
                  <Shield className="h-4 w-4 text-indigo-500" />
                </div>
                <div className="text-3xl font-bold">{overview.authority_score}</div>
                <p className="text-[10px] text-muted-foreground mt-1 uppercase tracking-wider font-semibold">Based on link quality</p>
              </CardContent>
            </Card>
            
            <Card className="bg-gradient-to-br from-emerald-50 to-transparent dark:from-emerald-950/20 border-emerald-100 dark:border-emerald-900">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between pb-2">
                  <p className="text-sm font-medium text-emerald-600 dark:text-emerald-400">Organic Traffic</p>
                  <Users className="h-4 w-4 text-emerald-500" />
                </div>
                <div className="text-3xl font-bold">{overview.organic_traffic.toLocaleString()}</div>
                <p className="text-[10px] text-muted-foreground mt-1 uppercase tracking-wider font-semibold">/ month (estimated)</p>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-amber-50 to-transparent dark:from-amber-950/20 border-amber-100 dark:border-amber-900">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between pb-2">
                  <p className="text-sm font-medium text-amber-600 dark:text-amber-400">Organic Keywords</p>
                  <Sparkles className="h-4 w-4 text-amber-500" />
                </div>
                <div className="text-3xl font-bold">{overview.organic_keywords.toLocaleString()}</div>
                <p className="text-[10px] text-muted-foreground mt-1 uppercase tracking-wider font-semibold">Ranking in Top 100</p>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-sky-50 to-transparent dark:from-sky-950/20 border-sky-100 dark:border-sky-900">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between pb-2">
                  <p className="text-sm font-medium text-sky-600 dark:text-sky-400">Backlinks</p>
                  <Link2 className="h-4 w-4 text-sky-500" />
                </div>
                <div className="text-3xl font-bold">{overview.backlinks_count.toLocaleString()}</div>
                <p className="text-[10px] text-muted-foreground mt-1 uppercase tracking-wider font-semibold">From {overview.referring_domains.toLocaleString()} domains</p>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Advertising Insights */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Target className="h-4 w-4 text-primary" />
                  Advertising Insights
                </CardTitle>
                <CardDescription>Paid search performance for {overview.domain}</CardDescription>
              </CardHeader>
              <CardContent className="grid grid-cols-3 gap-4">
                <div className="text-center p-4 rounded-lg bg-slate-50 dark:bg-slate-900">
                  <div className="text-sm font-medium text-muted-foreground mb-1">Paid Traffic</div>
                  <div className="text-xl font-bold">{overview.paid_traffic.toLocaleString()}</div>
                </div>
                <div className="text-center p-4 rounded-lg bg-slate-50 dark:bg-slate-900">
                  <div className="text-sm font-medium text-muted-foreground mb-1">Paid Keywords</div>
                  <div className="text-xl font-bold">{overview.paid_keywords.toLocaleString()}</div>
                </div>
                <div className="text-center p-4 rounded-lg bg-slate-50 dark:bg-slate-900">
                  <div className="text-sm font-medium text-muted-foreground mb-1">Display Ads</div>
                  <div className="text-xl font-bold">{overview.display_ads.toLocaleString()}</div>
                </div>
              </CardContent>
            </Card>

            {/* Main Competitors */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Organic Competitors</CardTitle>
                <CardDescription>Domains ranking for similar keywords</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {overview.main_competitors.map((comp, i) => (
                    <div key={i} className="flex items-center justify-between p-3 rounded-lg border hover:bg-slate-50 transition-colors">
                      <div className="flex items-center gap-3">
                         <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-xs font-bold text-slate-400">
                           {comp[0].toUpperCase()}
                         </div>
                         <span className="font-medium">{comp}</span>
                      </div>
                      <Button variant="ghost" size="icon" onClick={() => { setDomain(comp); setSearchDomain(comp); }}>
                        <ArrowRight className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="flex justify-center gap-4 py-4">
            <Button variant="outline" className="gap-2">
              <ExternalLink className="h-4 w-4" />
              View on Google
            </Button>
            <Button className="gap-2">
               Full Organic Report
               <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
