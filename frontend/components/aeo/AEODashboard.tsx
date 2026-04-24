/**
 * AEO Dashboard Component
 * Main dashboard for AI-Powered Search Engine Optimization
 */

'use client';

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Loader2, RefreshCw, AlertCircle, CheckCircle2 } from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';
import { api } from '@/lib/api';

import { AIVisibilityTracker } from './AIVisibilityTracker';
import { SnippetTracker } from './SnippetTracker';
import { ContentRecommendations } from './ContentRecommendations';
import { FAQGenerator } from './FAQGenerator';

interface AEOSummary {
  total_keywords: number;
  ai_visibility_count: number;
  featured_snippet_count: number;
  paa_queries_count: number;
  recommendation_count: number;
  pending_recommendations: number;
  implemented_recommendations: number;
  avg_ai_visibility_percentage: number;
  snippet_opportunities: number;
}

export function AEODashboard({ projectId: propProjectId }: { projectId?: string }) {
  const params = useParams();
  const projectId = propProjectId || params.id as string;
  const { toast } = useToast();

  const [summary, setSummary] = useState<AEOSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadSummary();
  }, [projectId]);

  const loadSummary = async () => {
    try {
      setLoading(true);
      const data = await api.aeo.getSummary(projectId);
      setSummary(data);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load AEO summary',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadSummary();
    setRefreshing(false);
    toast({
      title: 'Success',
      description: 'AEO data refreshed',
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">AEO Dashboard</h1>
          <p className="text-gray-600 mt-2">
            AI-Powered Search Engine Optimization Intelligence
          </p>
        </div>
        <Button
          onClick={handleRefresh}
          disabled={refreshing}
          variant="outline"
          size="sm"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Total Keywords
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{summary.total_keywords}</div>
              <p className="text-xs text-gray-500 mt-1">
                Being tracked
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                AI Visibility
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">
                {summary.avg_ai_visibility_percentage.toFixed(1)}%
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Average across models
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Featured Snippets
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{summary.featured_snippet_count}</div>
              <p className="text-xs text-gray-500 mt-1">
                {summary.snippet_opportunities} opportunities
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Recommendations
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">
                {summary.pending_recommendations}
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Pending action
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tab Navigation */}
      <Tabs defaultValue="visibility" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="visibility">AI Visibility</TabsTrigger>
          <TabsTrigger value="snippets">
            Snippets & PAA
            {summary && summary.snippet_opportunities > 0 && (
              <Badge variant="secondary" className="ml-2">
                {summary.snippet_opportunities}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="recommendations">
            Recommendations
            {summary && summary.pending_recommendations > 0 && (
              <Badge variant="secondary" className="ml-2">
                {summary.pending_recommendations}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="faq">FAQ Generator</TabsTrigger>
        </TabsList>

        {/* AI Visibility Tab */}
        <TabsContent value="visibility" className="space-y-4">
          <AIVisibilityTracker projectId={projectId} />
        </TabsContent>

        {/* Snippets & PAA Tab */}
        <TabsContent value="snippets" className="space-y-4">
          <SnippetTracker projectId={projectId} />
        </TabsContent>

        {/* Recommendations Tab */}
        <TabsContent value="recommendations" className="space-y-4">
          <ContentRecommendations projectId={projectId} />
        </TabsContent>

        {/* FAQ Tab */}
        <TabsContent value="faq" className="space-y-4">
          <FAQGenerator projectId={projectId} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
