/**
 * FAQ Generator Component
 */

'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Loader2, CheckCircle2, Pencil, Trash2 } from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';
import { api } from '@/lib/api';

interface FAQ {
  id: string;
  question: string;
  answer: string;
  approved: boolean;
  created_at: string;
}

interface ContentOutline {
  keyword: string;
  outline: string[];
  estimated_word_count: number;
  key_topics: string[];
}

export function FAQGenerator({ projectId }: { projectId: string }) {
  const [faqs, setFAQs] = useState<FAQ[]>([]);
  const [outline, setOutline] = useState<ContentOutline | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    loadFAQs();
  }, [projectId]);

  const loadFAQs = async () => {
    try {
      setLoading(true);
      const data = await api.aeo.getFAQs(projectId);
      setFAQs(data);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load FAQs',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateOutline = async () => {
    try {
      setGenerating(true);
      // Note: This would need a selected keyword in a real implementation
      toast({
        title: 'Info',
        description: 'Select a keyword to generate outline',
        variant: 'default',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to generate outline',
        variant: 'destructive',
      });
    } finally {
      setGenerating(false);
    }
  };

  const handleApproveFAQ = async (faqId: string) => {
    try {
      await api.aeo.approveFAQ(faqId);
      
      toast({
        title: 'Success',
        description: 'FAQ approved',
      });
      loadFAQs();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to approve FAQ',
        variant: 'destructive',
      });
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-6 w-6 animate-spin" />
      </div>
    );
  }

  const pending = faqs.filter((f) => !f.approved);
  const approved = faqs.filter((f) => f.approved);

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-2xl font-bold">FAQ Generator</h2>
        <p className="text-gray-600">Generate and manage FAQ entries for your content</p>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2">
        <Button onClick={handleGenerateOutline} disabled={generating}>
          {generating && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
          Generate from PAA
        </Button>
        <Button variant="outline">
          Generate Outline
        </Button>
      </div>

      {/* FAQ Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-amber-600">{pending.length}</div>
            <p className="text-xs text-gray-500 mt-1">Awaiting review</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Approved</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">{approved.length}</div>
            <p className="text-xs text-gray-500 mt-1">Ready to publish</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{faqs.length}</div>
            <p className="text-xs text-gray-500 mt-1">Generated</p>
          </CardContent>
        </Card>
      </div>

      {/* Pending FAQs */}
      {pending.length > 0 && (
        <div className="space-y-3">
          <h3 className="font-semibold text-lg">Pending Review</h3>
          {pending.map((faq) => (
            <Card key={faq.id} className="border-l-4 border-l-amber-500">
              <CardContent className="pt-6">
                <div className="space-y-3">
                  <div>
                    <div className="font-semibold text-base mb-2">{faq.question}</div>
                    <p className="text-sm text-gray-700 leading-relaxed">{faq.answer}</p>
                  </div>

                  <div className="flex gap-2 pt-2">
                    <Button
                      size="sm"
                      variant="default"
                      onClick={() => handleApproveFAQ(faq.id)}
                    >
                      <CheckCircle2 className="h-4 w-4 mr-1" />
                      Approve
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setEditingId(faq.id)}
                    >
                      <Pencil className="h-4 w-4 mr-1" />
                      Edit
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="text-red-600"
                    >
                      <Trash2 className="h-4 w-4 mr-1" />
                      Delete
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Approved FAQs */}
      {approved.length > 0 && (
        <div className="space-y-3">
          <h3 className="font-semibold text-lg">Approved ({approved.length})</h3>
          {approved.map((faq) => (
            <Card key={faq.id} className="bg-green-50 border-green-200">
              <CardContent className="pt-6">
                <div className="space-y-2">
                  <div className="flex items-start gap-2">
                    <CheckCircle2 className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <div className="font-semibold text-green-900">{faq.question}</div>
                      <p className="text-sm text-green-800 mt-1 leading-relaxed">{faq.answer}</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Empty State */}
      {faqs.length === 0 && (
        <Card className="border-dashed">
          <CardContent className="pt-6">
            <div className="text-center space-y-3">
              <p className="font-medium">No FAQs yet</p>
              <p className="text-sm text-gray-600">
                Generate FAQs from People Also Ask queries or create them manually
              </p>
              <Button variant="outline">Generate from PAA</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Content Outline Section */}
      {outline && (
        <Card>
          <CardHeader>
            <CardTitle>Content Outline - {outline.keyword}</CardTitle>
            <CardDescription>
              Estimated length: {outline.estimated_word_count} words
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h4 className="font-semibold mb-2">Outline</h4>
              <ol className="space-y-1 list-decimal list-inside">
                {outline.outline.map((item, idx) => (
                  <li key={idx} className="text-sm text-gray-700">{item}</li>
                ))}
              </ol>
            </div>

            <div>
              <h4 className="font-semibold mb-2">Key Topics</h4>
              <div className="flex flex-wrap gap-2">
                {outline.key_topics.map((topic) => (
                  <Badge key={topic} variant="outline">{topic}</Badge>
                ))}
              </div>
            </div>

            <Button className="w-full">Use This Outline</Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
