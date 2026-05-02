'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { 
  FileSearch, Search, Calendar, User, Share2, 
  Twitter, Facebook, Linkedin, Link2, ExternalLink, MousePointer2 
} from 'lucide-react';
import { useContentExplorer } from '@/hooks/useSEO';
import { format } from 'date-fns';

export function ContentExplorer({ projectId }: { projectId: string }) {
  const [query, setQuery] = useState('');
  const [searchQuery, setSearchQuery] = useState<string | null>(null);
  
  const { data: results, isLoading, isError } = useContentExplorer(searchQuery);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query) {
      setSearchQuery(query);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileSearch className="h-5 w-5 text-primary" />
            Content Explorer
          </CardTitle>
          <CardDescription>
            Find the most shared and linked-to content for any topic or keyword.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearch} className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Enter topic (e.g. AI Marketing)"
                className="pl-8"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </div>
            <Button type="submit" disabled={isLoading}>
              Search Content
            </Button>
          </form>
        </CardContent>
      </Card>

      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => <Skeleton key={i} className="h-80 w-full" />)}
        </div>
      )}

      {isError && (
        <Card className="border-destructive/50 bg-destructive/10">
          <CardContent className="py-6 text-center text-destructive">
            Failed to explore content. Please try again.
          </CardContent>
        </Card>
      )}

      {!results && !isLoading && !isError && (
        <div className="py-20 flex flex-col items-center justify-center text-center space-y-6 animate-in fade-in zoom-in duration-500">
          <div className="bg-primary/5 p-6 rounded-full ring-8 ring-primary/5">
            <FileSearch className="h-12 w-12 text-primary opacity-80" />
          </div>
          <div className="max-w-md space-y-2">
            <h3 className="text-xl font-bold">Reverse Engineer Viral Content</h3>
            <p className="text-muted-foreground text-sm leading-relaxed">
              Find the most shared and linked-to articles for any topic. 
              Discover what's working for your competitors and replicate their success.
            </p>
          </div>
          <div className="flex flex-wrap justify-center gap-2 pt-4">
            <Badge variant="secondary" className="px-3 py-1 cursor-pointer hover:bg-slate-200" onClick={() => { setQuery('SEO Trends 2026'); setSearchQuery('SEO Trends 2026'); }}>SEO Trends 2026</Badge>
            <Badge variant="secondary" className="px-3 py-1 cursor-pointer hover:bg-slate-200" onClick={() => { setQuery('AI Content Strategy'); setSearchQuery('AI Content Strategy'); }}>AI Content Strategy</Badge>
            <Badge variant="secondary" className="px-3 py-1 cursor-pointer hover:bg-slate-200" onClick={() => { setQuery('Link Building Hacks'); setSearchQuery('Link Building Hacks'); }}>Link Building Hacks</Badge>
          </div>
        </div>
      )}

      {results && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {results.articles.map((article) => (
            <Card key={article.id} className="flex flex-col hover:shadow-lg transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex justify-between items-start gap-2 mb-2">
                  <Badge variant="secondary" className="text-[10px] h-4">
                    {article.referring_domains} Ref. Domains
                  </Badge>
                  <div className="flex items-center gap-1 text-[10px] text-emerald-600 font-bold">
                    <MousePointer2 className="h-3 w-3" />
                    {article.est_organic_traffic.toLocaleString()} traffic
                  </div>
                </div>
                <CardTitle className="text-base leading-tight hover:text-primary cursor-pointer line-clamp-3">
                  <a href={article.url} target="_blank" rel="noopener noreferrer">
                    {article.title}
                  </a>
                </CardTitle>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col justify-between space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center gap-3 text-xs text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <User className="h-3 w-3" />
                      {article.author || 'Anonymous'}
                    </div>
                    <div className="flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      {format(new Date(article.published_at), 'MMM d, yyyy')}
                    </div>
                  </div>
                </div>

                <div className="pt-4 border-t space-y-3">
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-1 font-medium">
                      <Share2 className="h-3 w-3" />
                      Social Shares
                    </div>
                    <div className="font-bold text-primary">
                      {Object.values(article.social_shares).reduce((a, b) => a + b, 0).toLocaleString()}
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-1 text-[10px]">
                      <Twitter className="h-3 w-3 text-sky-400" />
                      {article.social_shares.twitter || 0}
                    </div>
                    <div className="flex items-center gap-1 text-[10px]">
                      <Facebook className="h-3 w-3 text-blue-600" />
                      {article.social_shares.facebook || 0}
                    </div>
                    <div className="flex items-center gap-1 text-[10px]">
                      <Linkedin className="h-3 w-3 text-blue-700" />
                      {article.social_shares.linkedin || 0}
                    </div>
                  </div>
                </div>

                <div className="flex gap-2 pt-2">
                  <Button size="sm" variant="outline" className="flex-1 h-8 text-[11px] gap-1" asChild>
                    <a href={article.url} target="_blank" rel="noopener noreferrer">
                      <ExternalLink className="h-3 w-3" />
                      View Original
                    </a>
                  </Button>
                  <Button size="sm" className="flex-1 h-8 text-[11px] gap-1">
                    <Link2 className="h-3 w-3" />
                    Analyze Links
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {results && results.articles.length === 0 && (
        <div className="py-12 text-center text-muted-foreground">
          No articles found for "{results.query}". Try a different topic.
        </div>
      )}
    </div>
  );
}
