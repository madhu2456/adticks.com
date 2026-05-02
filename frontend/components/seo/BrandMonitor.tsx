'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { 
  Bell, ExternalLink, Link as LinkIcon, Link2Off, 
  MessageSquare, Quote, ThumbsUp, ThumbsDown, Minus 
} from 'lucide-react';
import { useBrandMonitor } from '@/hooks/useSEO';
import { formatDistanceToNow } from 'date-fns';

export function BrandMonitor({ projectId }: { projectId: string }) {
  const { data: brandData, isLoading, isError } = useBrandMonitor(projectId);

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return <ThumbsUp className="h-3 w-3 text-emerald-500" />;
      case 'negative': return <ThumbsDown className="h-3 w-3 text-red-500" />;
      default: return <Minus className="h-3 w-3 text-slate-400" />;
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'negative': return 'bg-red-50 text-red-700 border-red-200';
      default: return 'bg-slate-50 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5 text-primary" />
            Brand Monitoring
          </CardTitle>
          <CardDescription>
            Track unlinked brand mentions across news, blogs, and social web.
          </CardDescription>
        </CardHeader>
      </Card>

      {isLoading && (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => <Skeleton key={i} className="h-32 w-full" />)}
        </div>
      )}

      {isError && (
        <Card className="border-destructive/50 bg-destructive/10">
          <CardContent className="py-6 text-center text-destructive">
            Failed to fetch brand mentions.
          </CardContent>
        </Card>
      )}

      <div className="space-y-4">
        {brandData?.mentions.map((mention) => (
          <Card key={mention.id} className="hover:border-primary/50 transition-colors overflow-hidden">
            <CardContent className="p-0">
              <div className="flex">
                {/* Sentiment & Status Sidebar */}
                <div className={`w-1.5 ${
                  mention.sentiment === 'positive' ? 'bg-emerald-500' : 
                  mention.sentiment === 'negative' ? 'bg-red-500' : 'bg-slate-300'
                }`} />
                
                <div className="p-5 flex-1 space-y-3">
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm">{mention.source_name}</span>
                        <Badge variant="outline" className="text-[10px] h-4">
                          DA: {mention.domain_authority}
                        </Badge>
                        <Badge variant="outline" className={`text-[10px] h-4 flex items-center gap-1 ${getSentimentColor(mention.sentiment)}`}>
                          {getSentimentIcon(mention.sentiment)}
                          {mention.sentiment}
                        </Badge>
                      </div>
                      <a 
                        href={mention.source_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-xs text-muted-foreground hover:text-primary flex items-center gap-1"
                      >
                        {mention.source_url}
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    </div>
                    <div className="text-right">
                      <div className="text-[10px] text-muted-foreground">
                        {formatDistanceToNow(new Date(mention.published_at), { addSuffix: true })}
                      </div>
                      <div className="mt-1">
                        {mention.is_linked ? (
                          <Badge className="bg-emerald-100 text-emerald-800 hover:bg-emerald-100 border-none flex items-center gap-1 text-[10px]">
                            <LinkIcon className="h-3 w-3" />
                            Linked
                          </Badge>
                        ) : (
                          <Badge variant="secondary" className="bg-amber-100 text-amber-800 hover:bg-amber-100 border-none flex items-center gap-1 text-[10px]">
                            <Link2Off className="h-3 w-3" />
                            Unlinked
                          </Badge>
                        )
                      }
                      </div>
                    </div>
                  </div>

                  <div className="relative pl-6 py-2 italic text-sm text-slate-600 bg-slate-50/50 rounded">
                    <Quote className="absolute left-1 top-2 h-4 w-4 text-slate-300" />
                    {mention.snippet}
                  </div>

                  <div className="flex items-center justify-end gap-2 pt-1">
                    {!mention.is_linked && (
                      <Button size="sm" variant="outline" className="h-8 text-xs gap-1 border-primary/30 text-primary hover:bg-primary/5">
                        <LinkIcon className="h-3 w-3" />
                        Reclaim Link
                      </Button>
                    )}
                    <Button size="sm" variant="ghost" className="h-8 text-xs gap-1">
                      <MessageSquare className="h-3 w-3" />
                      View Context
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}

        {!isLoading && (!brandData || brandData.mentions.length === 0) && (
          <div className="py-20 flex flex-col items-center justify-center text-center space-y-6 animate-in fade-in zoom-in duration-500">
            <div className="bg-primary/5 p-6 rounded-full ring-8 ring-primary/5">
              <Bell className="h-12 w-12 text-primary opacity-80" />
            </div>
            <div className="max-w-md space-y-2">
              <h3 className="text-xl font-bold">Monitor Your Reputation</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">
                We're currently crawling the web for mentions of your brand. 
                New mentions from news, blogs, and social platforms will appear here in real-time.
              </p>
            </div>
            <Button variant="outline" className="mt-4">
              Configure Alerts
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
