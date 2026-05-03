'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Megaphone, Search, DollarSign, Target, ExternalLink } from 'lucide-react';
import { useCompetitorPPC } from '@/hooks/useSEO';

export function PPCResearch({ projectId }: { projectId: string }) {
  const [domain, setDomain] = useState('');
  const [searchDomain, setSearchDomain] = useState<string | null>(null);
  
  // If searching own domain, pass projectId for real data
  const isOwnDomain = searchDomain === projectId; // You'd need to get actual project domain
  const { data: ppc, isLoading, isError } = useCompetitorPPC(
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
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Megaphone className="h-5 w-5 text-primary" />
            PPC Research
          </CardTitle>
          <CardDescription>
            Spy on competitors' paid search strategy and ad copies.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearch} className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Enter domain (e.g. competitor.com)"
                className="pl-8"
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
              />
            </div>
            <Button type="submit" disabled={isLoading}>
              Discover Ads
            </Button>
          </form>
        </CardContent>
      </Card>

      {isLoading && <Skeleton className="h-[400px] w-full" />}

      {isError && (
        <Card className="border-destructive/50 bg-destructive/10">
          <CardContent className="py-6 text-center text-destructive">
            Failed to fetch PPC data. Please try again with a valid domain.
          </CardContent>
        </Card>
      )}

      {!ppc && !isLoading && !isError && (
        <div className="py-20 flex flex-col items-center justify-center text-center space-y-6 animate-in fade-in zoom-in duration-500">
          <div className="bg-primary/5 p-6 rounded-full ring-8 ring-primary/5">
            <Megaphone className="h-12 w-12 text-primary opacity-80" />
          </div>
          <div className="max-w-md space-y-2">
            <h3 className="text-xl font-bold">Spy on Competitor Ads</h3>
            <p className="text-muted-foreground text-sm leading-relaxed">
              Discover the paid keywords your competitors are bidding on, 
              their estimated ad spend, and their actual ad copy.
            </p>
          </div>
          <div className="flex flex-wrap justify-center gap-2 pt-4">
            <Badge variant="secondary" className="px-3 py-1 cursor-pointer hover:bg-slate-200" onClick={() => { setDomain('nike.com'); setSearchDomain('nike.com'); }}>nike.com</Badge>
            <Badge variant="secondary" className="px-3 py-1 cursor-pointer hover:bg-slate-200" onClick={() => { setDomain('adidas.com'); setSearchDomain('adidas.com'); }}>adidas.com</Badge>
            <Badge variant="secondary" className="px-3 py-1 cursor-pointer hover:bg-slate-200" onClick={() => { setDomain('puma.com'); setSearchDomain('puma.com'); }}>puma.com</Badge>
          </div>
        </div>
      )}

      {ppc && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between space-y-0 pb-2">
                  <p className="text-sm font-medium">Est. Monthly Spend</p>
                  <DollarSign className="h-4 w-4 text-muted-foreground" />
                </div>
                <div className="text-2xl font-bold">${ppc.est_monthly_spend_usd.toLocaleString()}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  Based on keyword volume and CPC
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between space-y-0 pb-2">
                  <p className="text-sm font-medium">Paid Keywords</p>
                  <Target className="h-4 w-4 text-muted-foreground" />
                </div>
                <div className="text-2xl font-bold">{ppc.paid_keywords_count.toLocaleString()}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  Unique keywords triggering ads
                </p>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Paid Keywords Table */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Top Paid Keywords</CardTitle>
                <CardDescription>Keywords bringing most paid traffic to {ppc.domain}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="rounded-md border">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-muted/50">
                        <th className="p-3 text-left font-medium">Keyword</th>
                        <th className="p-3 text-right font-medium">Pos</th>
                        <th className="p-3 text-right font-medium">CPC</th>
                        <th className="p-3 text-right font-medium">Traffic %</th>
                      </tr>
                    </thead>
                    <tbody>
                      {ppc.top_paid_keywords.map((kw, i) => (
                        <tr key={i} className="border-b">
                          <td className="p-3">
                            <div className="font-medium">{kw.keyword}</div>
                            <div className="text-[10px] text-muted-foreground truncate max-w-[200px]">{kw.url}</div>
                          </td>
                          <td className="p-3 text-right">
                            <Badge variant={kw.position === 1 ? "default" : "secondary"}>
                              {kw.position}
                            </Badge>
                          </td>
                          <td className="p-3 text-right">${kw.cpc_usd.toFixed(2)}</td>
                          <td className="p-3 text-right">{(kw.traffic_share * 100).toFixed(1)}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>

            {/* Ad Samples */}
            <Card>
              <CardHeader>
                <CardTitle>Sample Ad Copy</CardTitle>
                <CardDescription>Actual ads found in SERP</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {ppc.sample_ads.map((ad, i) => (
                  <div key={i} className="p-4 rounded-lg border bg-card hover:shadow-md transition-shadow">
                    <div className="flex items-center gap-1 text-[10px] text-emerald-700 font-bold mb-1">
                      <span>Ad</span>
                      <span className="text-gray-400">•</span>
                      <span>{ad.visible_url}</span>
                    </div>
                    <h4 className="text-blue-700 font-medium hover:underline cursor-pointer mb-1">
                      {ad.title}
                    </h4>
                    <p className="text-xs text-gray-600 leading-relaxed">
                      {ad.description}
                    </p>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
