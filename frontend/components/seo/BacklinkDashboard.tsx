'use client';

import React, { useState } from 'react';
import { useTheme } from 'next-themes';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { 
  useBacklinks, 
  useBacklinkStats, 
  useBacklinkIntersect 
} from '@/hooks/useSEO';
import { 
  Link2, 
  Unlink, 
  Anchor, 
  ArrowUpRight, 
  ShieldCheck,
  Search,
  ExternalLink,
  Target,
  X
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface BacklinkDashboardProps {
  projectId: string;
}

export function BacklinkDashboard({ projectId }: BacklinkDashboardProps) {
  const { theme } = useTheme();
  const [currentPage, setCurrentPage] = useState(0);
  const [activeTab, setActiveTab] = useState("overview");
  const [minAuthority, setMinAuthority] = useState<number | ''>('');
  const pageSize = 15;
  const skip = currentPage * pageSize;

  // Fetch real data
  const { data: backlinksResponse, isLoading: backlinksLoading } = useBacklinks(
    projectId, 
    skip, 
    pageSize, 
    minAuthority === '' ? undefined : Number(minAuthority)
  );
  const { data: stats, isLoading: statsLoading } = useBacklinkStats(projectId);
  const { data: intersect, isLoading: intersectLoading } = useBacklinkIntersect(projectId);

  const isDark = theme === 'dark';
  const backlinks = backlinksResponse?.data || [];
  const totalCount = backlinksResponse?.total || 0;
  const totalPages = Math.ceil(totalCount / pageSize);

  const getAuthorityBadgeColor = (score: number) => {
    if (score >= 80) return 'text-green-500 bg-green-500/10 border-green-500/20';
    if (score >= 60) return 'text-blue-500 bg-blue-500/10 border-blue-500/20';
    if (score >= 40) return 'text-yellow-500 bg-yellow-500/10 border-yellow-500/20';
    return 'text-red-500 bg-red-500/10 border-red-500/20';
  };

  const handleMinAuthorityChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    if (val === '') {
      setMinAuthority('');
    } else {
      const num = parseInt(val);
      if (!isNaN(num)) {
        setMinAuthority(num);
      }
    }
    setCurrentPage(0); // Reset to first page on filter change
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xl font-bold text-text-primary">Backlinks Overview</h3>
          <p className="text-sm text-text-muted">Analyze your link profile and find gaps compared to competitors</p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="anchors">Anchor Text</TabsTrigger>
          <TabsTrigger value="intersect">Link Intersect</TabsTrigger>
        </TabsList>

        {/* --- Overview Tab --- */}
        <TabsContent value="overview" className="space-y-6 pt-4">
          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-4 flex items-center gap-4">
                <div className="p-3 bg-blue-500/10 rounded-lg text-blue-500">
                  <Link2 size={20} />
                </div>
                <div>
                  <p className="text-xs text-text-muted">Total Backlinks</p>
                  <p className="text-xl font-bold">{stats?.total_backlinks || 0}</p>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 flex items-center gap-4">
                <div className="p-3 bg-green-500/10 rounded-lg text-green-500">
                  <ArrowUpRight size={20} />
                </div>
                <div>
                  <p className="text-xs text-text-muted">New (30d)</p>
                  <p className="text-xl font-bold text-green-500">+{stats?.new_domains_30d || 0}</p>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 flex items-center gap-4">
                <div className="p-3 bg-red-500/10 rounded-lg text-red-500">
                  <Unlink size={20} />
                </div>
                <div>
                  <p className="text-xs text-text-muted">Lost (30d)</p>
                  <p className="text-xl font-bold text-red-500">-{stats?.lost_domains_30d || 0}</p>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 flex items-center gap-4">
                <div className="p-3 bg-purple-500/10 rounded-lg text-purple-500">
                  <ShieldCheck size={20} />
                </div>
                <div>
                  <p className="text-xs text-text-muted">Avg Authority</p>
                  <p className="text-xl font-bold">{(stats?.avg_authority || 0).toFixed(1)}</p>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader className="pb-3 border-b border-border flex flex-row items-center justify-between space-y-0">
              <CardTitle className="text-lg">Recent Backlinks</CardTitle>
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-text-muted" />
                  <Input
                    type="number"
                    placeholder="Filter by min authority"
                    className="h-8 w-[180px] pl-8 text-xs bg-surface-2"
                    value={minAuthority}
                    onChange={handleMinAuthorityChange}
                  />
                  {minAuthority !== '' && (
                    <button 
                      onClick={() => setMinAuthority('')}
                      className="absolute right-2 top-2 text-text-muted hover:text-text-primary"
                    >
                      <X size={14} />
                    </button>
                  )}
                </div>
                <Button variant="ghost" size="sm" className="h-8 text-xs" onClick={() => setMinAuthority('')}>
                  Clear
                </Button>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-surface2 border-b border-border">
                    <tr className="text-left text-xs font-semibold text-text-muted uppercase tracking-wider">
                      <th className="px-4 py-3">Referring Domain</th>
                      <th className="px-4 py-3">Authority</th>
                      <th className="px-4 py-3">First Seen</th>
                      <th className="px-4 py-3">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {backlinksLoading ? (
                      [1,2,3].map(i => (
                        <tr key={i}><td colSpan={4} className="px-4 py-4"><Skeleton className="h-4 w-full" /></td></tr>
                      ))
                    ) : backlinks.length > 0 ? (
                      backlinks.map((link) => (
                        <tr key={link.id} className="border-b border-border hover:bg-surface2/50 transition-colors">
                          <td className="px-4 py-4">
                            <div className="font-medium text-text-primary flex items-center gap-2">
                              {link.referring_domain}
                              <ExternalLink size={12} className="text-text-tertiary" />
                            </div>
                            <p className="text-xs text-text-muted truncate max-w-[200px]">{link.target_url || "Homepage"}</p>
                          </td>
                          <td className="px-4 py-4">
                            <Badge variant="outline" className={cn("font-bold", getAuthorityBadgeColor(link.authority_score))}>
                              {link.authority_score.toFixed(0)}
                            </Badge>
                          </td>
                          <td className="px-4 py-4 text-text-muted">
                            {new Date(link.timestamp).toLocaleDateString()}
                          </td>
                          <td className="px-4 py-4">
                            <Badge variant="secondary" className="capitalize">
                              {link.status || "active"}
                            </Badge>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={4} className="px-4 py-10 text-center text-text-muted">
                          No backlinks available
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
              
              {/* Pagination */}
              <div className="flex items-center justify-between p-4 border-t border-border">
                <p className="text-xs text-text-muted">Showing page {currentPage + 1} of {totalPages || 1}</p>
                <div className="flex gap-2">
                  <Button 
                    variant="outline" size="sm" 
                    disabled={currentPage === 0}
                    onClick={() => setCurrentPage(prev => prev - 1)}
                  >Previous</Button>
                  <Button 
                    variant="outline" size="sm"
                    disabled={currentPage >= totalPages - 1}
                    onClick={() => setCurrentPage(prev => prev + 1)}
                  >Next</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* --- Anchors Tab --- */}
        <TabsContent value="anchors" className="pt-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Anchor className="h-5 w-5 text-primary" />
                Anchor Text Distribution
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {(stats?.top_anchor_texts || []).map((anchor: any, idx: number) => (
                   <div key={idx} className="space-y-2">
                     <div className="flex justify-between text-sm">
                       <span className="font-medium">{anchor.text}</span>
                       <span className="text-text-muted">{anchor.count} links</span>
                     </div>
                     <div className="h-2 bg-surface2 rounded-full overflow-hidden">
                       <div 
                        className="h-full bg-primary" 
                        style={{ width: `${Math.min(100, (anchor.count / stats.total_backlinks) * 100)}%` }} 
                       />
                     </div>
                   </div>
                ))}
                {!stats?.top_anchor_texts?.length && (
                  <div className="text-center py-10 text-text-muted italic">
                    No anchor text data available yet.
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* --- Intersect Tab --- */}
        <TabsContent value="intersect" className="pt-4">
          <Card>
            <CardHeader className="pb-3 border-b border-border">
              <CardTitle className="text-lg flex items-center gap-2">
                <Target className="h-5 w-5 text-primary" />
                Backlink Intersect (Gap Analysis)
              </CardTitle>
              <p className="text-sm text-text-muted">Domains that link to your competitors but not to you.</p>
            </CardHeader>
            <CardContent className="p-0">
               <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-surface2 border-b border-border">
                    <tr className="text-left text-xs font-semibold text-text-muted uppercase tracking-wider">
                      <th className="px-4 py-3">Potential Source</th>
                      <th className="px-4 py-3">Authority</th>
                      <th className="px-4 py-3">Links To</th>
                    </tr>
                  </thead>
                  <tbody>
                    {intersectLoading ? (
                       <tr><td colSpan={3} className="px-4 py-8 text-center"><Skeleton className="h-10 w-full" /></td></tr>
                    ) : (intersect || []).map((item, idx) => (
                      <tr key={idx} className="border-b border-border hover:bg-surface2/50">
                        <td className="px-4 py-4 font-medium text-text-primary">
                          {item.referring_domain}
                        </td>
                        <td className="px-4 py-4">
                          <Badge variant="outline" className={getAuthorityBadgeColor(item.authority_score)}>
                            {item.authority_score.toFixed(0)}
                          </Badge>
                        </td>
                        <td className="px-4 py-4">
                          <div className="flex items-center gap-1.5">
                            <div className="w-4 h-4 bg-primary/20 rounded-full flex items-center justify-center text-[10px] text-primary">C</div>
                            <span className="text-text-muted">{item.links_to_competitor}</span>
                          </div>
                        </td>
                      </tr>
                    ))}
                    {!intersectLoading && (!intersect || intersect.length === 0) && (
                      <tr><td colSpan={3} className="px-4 py-10 text-center text-text-muted italic">No link gaps identified.</td></tr>
                    )}
                  </tbody>
                </table>
               </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
