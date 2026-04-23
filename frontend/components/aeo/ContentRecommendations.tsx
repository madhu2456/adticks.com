/**
 * Content Recommendations Component
 */

'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Loader2, CheckCircle2, XCircle, ArrowRight } from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';

interface Recommendation {
  id: string;
  recommendation_type: string;
  recommendation_text: string;
  implementation_difficulty: string;
  estimated_impact: string;
  user_action?: string;
}

const difficultyColors = {
  easy: 'bg-green-100 text-green-800',
  medium: 'bg-yellow-100 text-yellow-800',
  hard: 'bg-red-100 text-red-800',
};

const impactColors = {
  low: 'bg-gray-100 text-gray-800',
  medium: 'bg-blue-100 text-blue-800',
  high: 'bg-purple-100 text-purple-800',
};

export function ContentRecommendations({ projectId }: { projectId: string }) {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [marking, setMarking] = useState<string | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    loadRecommendations();
  }, [projectId]);

  const loadRecommendations = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `/api/aeo/projects/${projectId}/recommendations`,
        {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        }
      );

      if (response.ok) {
        const data = await response.json();
        setRecommendations(data);
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load recommendations',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAction = async (
    recommendationId: string,
    action: 'implemented' | 'rejected'
  ) => {
    try {
      setMarking(recommendationId);
      const response = await fetch(
        `/api/aeo/recommendations/${recommendationId}`,
        {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ user_action: action }),
        }
      );

      if (response.ok) {
        toast({
          title: 'Success',
          description: `Recommendation marked as ${action}`,
        });
        loadRecommendations();
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to update recommendation',
        variant: 'destructive',
      });
    } finally {
      setMarking(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-6 w-6 animate-spin" />
      </div>
    );
  }

  const pending = recommendations.filter((r) => !r.user_action);
  const implemented = recommendations.filter((r) => r.user_action === 'implemented');
  const rejected = recommendations.filter((r) => r.user_action === 'rejected');

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-2xl font-bold">Content Recommendations</h2>
        <p className="text-gray-600">AI-powered suggestions to improve your content</p>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-amber-600">{pending.length}</div>
            <p className="text-xs text-gray-500 mt-1">Awaiting action</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Implemented</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">{implemented.length}</div>
            <p className="text-xs text-gray-500 mt-1">Completed</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Rejected</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-600">{rejected.length}</div>
            <p className="text-xs text-gray-500 mt-1">Passed</p>
          </CardContent>
        </Card>
      </div>

      {/* Recommendations List */}
      <div className="space-y-3">
        {pending.length > 0 ? (
          <>
            <h3 className="font-semibold text-lg">Pending Recommendations</h3>
            {pending.map((rec) => (
              <Card key={rec.id} className="border-l-4 border-l-amber-500">
                <CardContent className="pt-6">
                  <div className="space-y-3">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <Badge className="mb-2">
                          {rec.recommendation_type}
                        </Badge>
                        <p className="text-sm font-medium mt-2">
                          {rec.recommendation_text}
                        </p>
                      </div>
                    </div>

                    <div className="flex gap-2 flex-wrap">
                      <Badge
                        className={difficultyColors[rec.implementation_difficulty as keyof typeof difficultyColors]}
                        variant="outline"
                      >
                        Difficulty: {rec.implementation_difficulty}
                      </Badge>
                      <Badge
                        className={impactColors[rec.estimated_impact as keyof typeof impactColors]}
                        variant="outline"
                      >
                        Impact: {rec.estimated_impact}
                      </Badge>
                    </div>

                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="default"
                        onClick={() => handleMarkAction(rec.id, 'implemented')}
                        disabled={marking === rec.id}
                      >
                        {marking === rec.id && (
                          <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                        )}
                        Mark Implemented
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleMarkAction(rec.id, 'rejected')}
                        disabled={marking === rec.id}
                      >
                        Dismiss
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </>
        ) : (
          <Card className="bg-green-50 border-green-200">
            <CardContent className="pt-6">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-green-600" />
                <p className="text-green-800">All recommendations have been addressed!</p>
              </div>
            </CardContent>
          </Card>
        )}

        {implemented.length > 0 && (
          <div className="mt-6">
            <h3 className="font-semibold text-lg mb-3">Implemented ({implemented.length})</h3>
            <div className="space-y-2">
              {implemented.map((rec) => (
                <div
                  key={rec.id}
                  className="p-3 bg-green-50 border border-green-200 rounded-lg flex items-start gap-2"
                >
                  <CheckCircle2 className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-green-900">
                      {rec.recommendation_text.substring(0, 60)}...
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Getting Started Card */}
      {pending.length === 0 && implemented.length === 0 && (
        <Card className="border-dashed">
          <CardContent className="pt-6">
            <div className="text-center space-y-3">
              <p className="font-medium">No recommendations yet</p>
              <p className="text-sm text-gray-600">
                Select a keyword to generate AI-powered recommendations
              </p>
              <Button variant="outline">Browse Keywords</Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
