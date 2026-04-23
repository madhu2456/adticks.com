/**
 * Snippet Tracker Component
 * Featured snippets and People Also Ask tracking
 */

'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { AlertCircle, CheckCircle2, HelpCircle, Loader2 } from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';

interface SnippetData {
  has_snippet: boolean;
  snippet_type?: string;
  snippet_text?: string;
  position?: number;
  date_captured: string;
}

interface PAA_Query {
  paa_query: string;
  answer_source_url?: string;
  position?: number;
  date_found: string;
}

interface SnippetSummary {
  total_keywords: number;
  with_snippet: number;
  without_snippet: number;
  lost_snippet: number;
  snippet_percentage: number;
}

export function SnippetTracker({ projectId }: { projectId: string }) {
  const [summary, setSummary] = useState<SnippetSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    loadSnippetData();
  }, [projectId]);

  const loadSnippetData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');

      const response = await fetch(
        `/api/aeo/projects/${projectId}/snippets/summary`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );

      if (response.ok) {
        const data = await response.json();
        setSummary(data);
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load snippet data',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-6 w-6 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-2xl font-bold">Featured Snippets & PAA</h2>
        <p className="text-gray-600">Monitor snippet status and People Also Ask opportunities</p>
      </div>

      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">With Snippet</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="text-3xl font-bold">{summary.with_snippet}</div>
                <CheckCircle2 className="h-8 w-8 text-green-500" />
              </div>
              <p className="text-xs text-gray-500 mt-2">
                {(summary.snippet_percentage).toFixed(1)}% of keywords
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Without Snippet</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="text-3xl font-bold">{summary.without_snippet}</div>
                <AlertCircle className="h-8 w-8 text-amber-500" />
              </div>
              <p className="text-xs text-gray-500 mt-2">Optimization opportunity</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Lost Snippets</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="text-3xl font-bold">{summary.lost_snippet}</div>
                <AlertCircle className="h-8 w-8 text-red-500" />
              </div>
              <p className="text-xs text-gray-500 mt-2">Need attention</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Total Keywords</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{summary.total_keywords}</div>
              <p className="text-xs text-gray-500 mt-2">Tracked</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Featured Snippets Card */}
      <Card>
        <CardHeader>
          <CardTitle>Featured Snippet Opportunities</CardTitle>
          <CardDescription>
            Keywords without featured snippets but with ranking potential
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
              <div className="flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-semibold text-amber-900">
                    {summary?.without_snippet || 0} Keywords Without Snippets
                  </p>
                  <p className="text-sm text-amber-700 mt-1">
                    Optimize your content to match featured snippet format and increase visibility.
                  </p>
                </div>
              </div>
            </div>

            <Button className="w-full">View Opportunities</Button>
          </div>
        </CardContent>
      </Card>

      {/* PAA Queries Card */}
      <Card>
        <CardHeader>
          <CardTitle>People Also Ask Queries</CardTitle>
          <CardDescription>Common questions your keywords appear for</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center gap-3">
                <HelpCircle className="h-5 w-5 text-blue-600" />
                <div>
                  <p className="font-semibold text-blue-900">FAQ Opportunities</p>
                  <p className="text-sm text-blue-700">
                    Create FAQ sections to answer PAA queries
                  </p>
                </div>
              </div>
              <Badge variant="outline">Generate</Badge>
            </div>

            <Button className="w-full">Generate FAQ from PAA</Button>
          </div>
        </CardContent>
      </Card>

      {/* Snippet Optimization Tips */}
      <Card>
        <CardHeader>
          <CardTitle>Snippet Optimization Tips</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-3 text-sm">
            <li className="flex gap-2">
              <span className="text-primary font-semibold">•</span>
              <span>Target position 1-5 for highest snippet probability</span>
            </li>
            <li className="flex gap-2">
              <span className="text-primary font-semibold">•</span>
              <span>Use descriptive headings and subheadings</span>
            </li>
            <li className="flex gap-2">
              <span className="text-primary font-semibold">•</span>
              <span>Keep answers concise (40-60 words)</span>
            </li>
            <li className="flex gap-2">
              <span className="text-primary font-semibold">•</span>
              <span>Use lists, tables, and definitions when appropriate</span>
            </li>
            <li className="flex gap-2">
              <span className="text-primary font-semibold">•</span>
              <span>Include relevant images and alt text</span>
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
