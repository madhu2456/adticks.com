'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  PieChart, Pie, Cell, Legend 
} from 'recharts';
import { Globe, TrendingUp, Users, MousePointer2, Clock, Search } from 'lucide-react';
import { useTrafficAnalytics } from '@/hooks/useSEO';

export function TrafficAnalytics({ projectId }: { projectId: string }) {
  const [domain, setDomain] = useState('');
  const [searchDomain, setSearchDomain] = useState<string | null>(null);
  
  // If searching own domain, pass projectId for real data
  const isOwnDomain = searchDomain === projectId; // You'd need to get actual project domain
  const { data: traffic, isLoading, isError } = useTrafficAnalytics(
    searchDomain,
    isOwnDomain ? projectId : undefined
  );

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (domain) {
      setSearchDomain(domain);
    }
  };

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

  const channelData = traffic ? [
    { name: 'Organic', value: traffic.organic_share * 100 },
    { name: 'Paid', value: traffic.paid_share * 100 },
    { name: 'Direct/Other', value: (1 - traffic.organic_share - traffic.paid_share) * 100 },
  ] : [];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="h-5 w-5 text-primary" />
            Traffic Analytics
          </CardTitle>
          <CardDescription>
            Estimate overall traffic and engagement for any domain.
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
              Analyze
            </Button>
          </form>
        </CardContent>
      </Card>

      {isLoading && <Skeleton className="h-[400px] w-full" />}

      {isError && (
        <Card className="border-destructive/50 bg-destructive/10">
          <CardContent className="py-6 text-center text-destructive">
            Failed to fetch traffic data. Please try again with a valid domain.
          </CardContent>
        </Card>
      )}

      {!traffic && !isLoading && !isError && (
        <div className="py-20 flex flex-col items-center justify-center text-center space-y-6 animate-in fade-in zoom-in duration-500">
          <div className="bg-primary/5 p-6 rounded-full ring-8 ring-primary/5">
            <Globe className="h-12 w-12 text-primary opacity-80" />
          </div>
          <div className="max-w-md space-y-2">
            <h3 className="text-xl font-bold">Uncover Competitor Insights</h3>
            <p className="text-muted-foreground text-sm leading-relaxed">
              Enter any domain above to reveal their estimated traffic volume, 
              top performing pages, and geographic distribution.
            </p>
          </div>
          <div className="flex flex-wrap justify-center gap-2 pt-4">
            <Badge variant="secondary" className="px-3 py-1 cursor-pointer hover:bg-slate-200" onClick={() => { setDomain('apple.com'); setSearchDomain('apple.com'); }}>apple.com</Badge>
            <Badge variant="secondary" className="px-3 py-1 cursor-pointer hover:bg-slate-200" onClick={() => { setDomain('semrush.com'); setSearchDomain('semrush.com'); }}>semrush.com</Badge>
            <Badge variant="secondary" className="px-3 py-1 cursor-pointer hover:bg-slate-200" onClick={() => { setDomain('hubspot.com'); setSearchDomain('hubspot.com'); }}>hubspot.com</Badge>
          </div>
        </div>
      )}

      {traffic && (
        <>
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between space-y-0 pb-2">
                  <p className="text-sm font-medium">Monthly Visits</p>
                  <Users className="h-4 w-4 text-muted-foreground" />
                </div>
                <div className="text-2xl font-bold">{traffic.monthly_visits.toLocaleString()}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  <TrendingUp className="inline h-3 w-3 text-emerald-500 mr-1" />
                  Estimated from global panel
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between space-y-0 pb-2">
                  <p className="text-sm font-medium">Avg. Duration</p>
                  <Clock className="h-4 w-4 text-muted-foreground" />
                </div>
                <div className="text-2xl font-bold">{Math.floor(traffic.engagement.avg_visit_duration_sec / 60)}m {traffic.engagement.avg_visit_duration_sec % 60}s</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between space-y-0 pb-2">
                  <p className="text-sm font-medium">Pages / Visit</p>
                  <MousePointer2 className="h-4 w-4 text-muted-foreground" />
                </div>
                <div className="text-2xl font-bold">{traffic.engagement.pages_per_visit.toFixed(2)}</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between space-y-0 pb-2">
                  <p className="text-sm font-medium">Bounce Rate</p>
                  <TrendingUp className="h-4 w-4 text-muted-foreground" />
                </div>
                <div className="text-2xl font-bold">{(traffic.engagement.bounce_rate * 100).toFixed(1)}%</div>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Traffic Sources */}
            <Card>
              <CardHeader>
                <CardTitle>Traffic Channels</CardTitle>
              </CardHeader>
              <CardContent className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={channelData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {channelData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Top Countries */}
            <Card>
              <CardHeader>
                <CardTitle>Top Countries</CardTitle>
              </CardHeader>
              <CardContent className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={traffic.top_countries} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" hide />
                    <YAxis dataKey="country" type="category" width={100} />
                    <Tooltip formatter={(value: number) => `${(value * 100).toFixed(1)}%`} />
                    <Bar dataKey="share" fill="#0ea5e9" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Top Pages */}
          <Card>
            <CardHeader>
              <CardTitle>Top Pages</CardTitle>
              <CardDescription>Most visited pages for {traffic.domain}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="rounded-md border">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="p-3 text-left font-medium">URL</th>
                      <th className="p-3 text-right font-medium">Traffic Share</th>
                      <th className="p-3 text-right font-medium">Avg. Duration</th>
                    </tr>
                  </thead>
                  <tbody>
                    {traffic.top_pages.map((page, i) => (
                      <tr key={i} className="border-b">
                        <td className="p-3 font-mono text-xs truncate max-w-md">
                          <a href={page.url} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                            {page.url}
                          </a>
                        </td>
                        <td className="p-3 text-right">{(page.traffic_share * 100).toFixed(1)}%</td>
                        <td className="p-3 text-right">{Math.floor(page.avg_duration_sec / 60)}m {page.avg_duration_sec % 60}s</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
