'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useTheme } from 'next-themes';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

interface CompetitorKeywordsData {
  id: string;
  project_id: string;
  competitor_domain: string;
  keywords: string[];
  count: number;
  timestamp: string;
}

interface PaginatedResponse<T> {
  data: T[];
  total: number;
  skip: number;
  limit: number;
  has_more: boolean;
}

interface CompetitorAnalysisProps {
  projectId: string;
  pageSize?: number;
}

export function CompetitorAnalysis({
  projectId,
  pageSize = 10,
}: CompetitorAnalysisProps) {
  const { theme } = useTheme();
  const [currentPage, setCurrentPage] = useState(0);
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  const skip = currentPage * pageSize;

  // Fetch competitor keywords
  const { data: response, isLoading, error } = useQuery({
    queryKey: ['competitorKeywords', projectId, skip],
    queryFn: async () => {
      const res = await axios.get(
        `/api/seo/projects/${projectId}/competitors/keywords?skip=${skip}&limit=${pageSize}`
      );
      return res.data as PaginatedResponse<CompetitorKeywordsData>;
    },
    staleTime: 60 * 60 * 1000, // 1 hour
  });

  const isDark = theme === 'dark';
  const bgColor = isDark ? 'bg-slate-900' : 'bg-white';
  const textColor = isDark ? 'text-slate-100' : 'text-slate-900';

  const toggleRowExpansion = (id: string) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedRows(newExpanded);
  };

  if (error) {
    return (
      <div className="flex items-center justify-center py-8 text-red-500">
        Failed to load competitor keywords
      </div>
    );
  }

  const competitors = response?.data || [];
  const totalPages = response
    ? Math.ceil(response.total / pageSize)
    : 0;

  return (
    <div className={`space-y-4 ${bgColor} rounded-lg p-4`}>
      <div className="space-y-2">
        <h3 className={`font-semibold ${textColor}`}>
          Competitor Keywords Analysis
        </h3>
        <p className="text-sm text-gray-500">
          Total competitors: {response?.total || 0}
        </p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-8">
          <div className="text-gray-500">Loading competitor data...</div>
        </div>
      ) : competitors.length === 0 ? (
        <div className="flex items-center justify-center py-8">
          <div className="text-gray-500">No competitor data available</div>
        </div>
      ) : (
        <>
          <div className="space-y-2">
            {competitors.map((competitor) => (
              <div
                key={competitor.id}
                className={`border rounded-lg p-3 ${isDark ? 'border-slate-700' : 'border-slate-200'}`}
              >
                <div className="flex justify-between items-center">
                  <div>
                    <p className={`font-medium ${textColor}`}>
                      {competitor.competitor_domain}
                    </p>
                    <p className="text-sm text-gray-500">
                      Keywords: {competitor.count}
                    </p>
                  </div>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => toggleRowExpansion(competitor.id)}
                  >
                    {expandedRows.has(competitor.id) ? 'Hide' : 'Show'}
                  </Button>
                </div>
                {expandedRows.has(competitor.id) && (
                  <div className="mt-3 pt-3 border-t">
                    <p className={`text-sm font-semibold ${textColor} mb-2`}>
                      Keywords:
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {competitor.keywords.slice(0, 20).map((keyword, idx) => (
                        <Badge key={idx} variant="secondary">
                          {keyword}
                        </Badge>
                      ))}
                      {competitor.keywords.length > 20 && (
                        <Badge variant="secondary">
                          +{competitor.keywords.length - 20} more
                        </Badge>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between mt-4">
            <div className={`text-sm ${textColor}`}>
              Page {currentPage + 1} of {totalPages}
            </div>
            <div className="flex gap-2">
              <Button
                onClick={() => setCurrentPage(currentPage - 1)}
                disabled={currentPage === 0}
                variant="outline"
                size="sm"
              >
                Previous
              </Button>
              <Button
                onClick={() => setCurrentPage(currentPage + 1)}
                disabled={currentPage >= totalPages - 1}
                variant="outline"
                size="sm"
              >
                Next
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
