/**
 * AI Visibility Tracker Component
 * Displays visibility in ChatGPT, Perplexity, and Claude
 */

'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Loader2, CheckCircle2, XCircle } from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';

interface VisibilityData {
  ai_model: string;
  is_mentioned: boolean;
  mention_context?: string;
  position?: number;
  confidence_score: number;
  timestamp: string;
}

interface VisibilitySummary {
  model: string;
  isMentioned: boolean;
  position?: number;
  confidence: number;
  context?: string;
}

export default function AIVisibilityTracker({ projectId }: { projectId: string }) {
  const [data, setData] = useState<VisibilitySummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [checking, setChecking] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    loadVisibilityData();
  }, [projectId]);

  const loadVisibilityData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');

      // Load data for each AI model
      const models = ['chatgpt', 'perplexity', 'claude'];
      const results: VisibilitySummary[] = [];

      for (const model of models) {
        const response = await fetch(
          `/api/aeo/projects/${projectId}/visibility/${model}?limit=1`,
          { headers: { 'Authorization': `Bearer ${token}` } }
        );

        if (response.ok) {
          const records = await response.json();
          if (records.length > 0) {
            const record = records[0];
            results.push({
              model: model.charAt(0).toUpperCase() + model.slice(1),
              isMentioned: record.is_mentioned,
              position: record.position,
              confidence: record.confidence_score,
              context: record.mention_context
            });
          }
        }
      }

      setData(results);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load visibility data',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCheckVisibility = async () => {
    try {
      setChecking(true);
      const response = await fetch('/api/aeo/check-visibility', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ai_models: ['chatgpt', 'perplexity', 'claude']
        }),
      });

      if (response.ok) {
        toast({
          title: 'Success',
          description: 'Visibility check queued',
        });
        setTimeout(() => loadVisibilityData(), 2000);
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to check visibility',
        variant: 'destructive',
      });
    } finally {
      setChecking(false);
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
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">AI Chatbot Visibility</h2>
          <p className="text-gray-600">Monitor your brand in ChatGPT, Perplexity, and Claude</p>
        </div>
        <Button 
          onClick={handleCheckVisibility} 
          disabled={checking}
        >
          {checking ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : null}
          Check Visibility
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {data.length > 0 ? (
          data.map((item) => (
            <Card key={item.model}>
              <CardHeader>
                <CardTitle className="text-lg">{item.model}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  {item.isMentioned ? (
                    <>
                      <CheckCircle2 className="h-6 w-6 text-green-500" />
                      <Badge variant="outline" className="bg-green-50">
                        Mentioned
                      </Badge>
                    </>
                  ) : (
                    <>
                      <XCircle className="h-6 w-6 text-gray-400" />
                      <Badge variant="outline">Not Mentioned</Badge>
                    </>
                  )}
                </div>

                {item.position && (
                  <div>
                    <p className="text-sm text-gray-600">Position</p>
                    <p className="text-2xl font-bold">#{item.position}</p>
                  </div>
                )}

                <div>
                  <div className="flex justify-between items-center mb-2">
                    <p className="text-sm text-gray-600">Confidence</p>
                    <span className="text-sm font-semibold">
                      {(item.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <Progress value={item.confidence * 100} />
                </div>

                {item.context && (
                  <div className="p-2 bg-gray-50 rounded text-xs text-gray-600">
                    "{item.context}"
                  </div>
                )}
              </CardContent>
            </Card>
          ))
        ) : (
          <Card className="col-span-full">
            <CardContent className="pt-6">
              <p className="text-center text-gray-500">No visibility data yet. Run a check to get started.</p>
            </CardContent>
          </Card>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Visibility Trends</CardTitle>
          <CardDescription>Track visibility over time</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-600">Trend data will appear here as you collect more checks over time.</p>
        </CardContent>
      </Card>
    </div>
  );
}
