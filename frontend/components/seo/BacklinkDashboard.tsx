'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useTheme } from 'next-themes';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';

interface BacklinksData {
  id: string;
  project_id: string;
  referring_domain: string;
  authority_score: number;
  timestamp: string;
}

interface PaginatedResponse<T> {
  data: T[];
  total: number;
  skip: number;
  limit: number;
  has_more: boolean;
}

interface BacklinkDashboardProps {
  projectId: string;
  pageSize?: number;
}

export function BacklinkDashboard({
  projectId,
  pageSize = 15,
}: BacklinkDashboardProps) {
  const { theme } = useTheme();
  const [currentPage, setCurrentPage] = useState(0);
  const [minAuthority, setMinAuthority] = useState<number | null>(null);

  const skip = currentPage * pageSize;

  // Fetch backlinks
  const { data: response, isLoading, error } = useQuery({
    queryKey: ['backlinks', projectId, skip, minAuthority],
    queryFn: async () => {
      const params = new URLSearchParams({
        skip: skip.toString(),
        limit: pageSize.toString(),
      });
      if (minAuthority !== null) {
        params.append('min_authority', minAuthority.toString());
      }

      const res = await axios.get(
        `/api/seo/projects/${projectId}/backlinks?${params}`
      );
      return res.data as PaginatedResponse<BacklinksData>;
    },
    staleTime: 60 * 60 * 1000, // 1 hour
  });

  const isDark = theme === 'dark';
  const bgColor = isDark ? 'bg-slate-900' : 'bg-white';
  const textColor = isDark ? 'text-slate-100' : 'text-slate-900';

  const getAuthorityBadgeColor = (score: number) => {
    if (score >= 80) return 'success';
    if (score >= 60) return 'primary';
    if (score >= 40) return 'warning';
    return 'danger';
  };

  const backlinks = response?.data || [];
  const totalPages = response
    ? Math.ceil(response.total / pageSize)
    : 0;

  const stats = {
    total: response?.total || 0,
    avgAuthority:
      backlinks.length > 0
        ? (
            backlinks.reduce((sum, b) => sum + b.authority_score, 0) /
            backlinks.length
          ).toFixed(2)
        : '0',
    topAuthority: backlinks.length > 0 ? backlinks[0].authority_score : 0,
  };

  if (error) {
    return (
      <div className="flex items-center justify-center py-8 text-red-500">
        Failed to load backlinks
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${bgColor} rounded-lg p-4`}>
      {/* Header */}
      <div className="space-y-2">
        <h3 className={`font-semibold ${textColor}`}>Backlinks Overview</h3>
        <p className="text-sm text-gray-500">
          Track referring domains and authority metrics
        </p>
      </div>

      {/* Stats Row */}
      {response && (
        <div className="grid grid-cols-3 gap-4 py-2">
          <div className={`p-3 rounded border ${isDark ? 'border-slate-700' : 'border-slate-200'}`}>
            <p className="text-xs text-gray-500 mb-1">Total Backlinks</p>
            <p className={`text-2xl font-bold ${textColor}`}>{stats.total}</p>
          </div>
          <div className={`p-3 rounded border ${isDark ? 'border-slate-700' : 'border-slate-200'}`}>
            <p className="text-xs text-gray-500 mb-1">Avg Authority</p>
            <p className={`text-2xl font-bold ${textColor}`}>{stats.avgAuthority}</p>
          </div>
          <div className={`p-3 rounded border ${isDark ? 'border-slate-700' : 'border-slate-200'}`}>
            <p className="text-xs text-gray-500 mb-1">Top Authority</p>
            <p className={`text-2xl font-bold ${textColor}`}>{stats.topAuthority}</p>
          </div>
        </div>
      )}

      {/* Filter */}
      <div className="space-y-2">
        <label className={`text-sm font-medium ${textColor}`}>
          Minimum Authority Score
        </label>
        <div className="flex gap-2">
          <Input
            type="number"
            min="0"
            max="100"
            value={minAuthority ?? ''}
            onChange={(e) =>
              setMinAuthority(e.target.value === '' ? null : parseInt(e.target.value))
            }
            placeholder="Filter by min authority (0-100)"
          />
          <Button
            onClick={() => setMinAuthority(null)}
            variant="outline"
            size="sm"
          >
            Clear
          </Button>
        </div>
      </div>

      {/* List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-8">
          <div className="text-gray-500">Loading backlinks...</div>
        </div>
      ) : backlinks.length === 0 ? (
        <div className="flex items-center justify-center py-8">
          <div className="text-gray-500">
            {minAuthority !== null
              ? `No backlinks with authority >= ${minAuthority}`
              : 'No backlinks available'}
          </div>
        </div>
      ) : (
        <>
          <div className="space-y-2">
            {backlinks.map((backlink) => (
              <div
                key={backlink.id}
                className={`flex justify-between items-center p-3 rounded-lg border ${isDark ? 'border-slate-700' : 'border-slate-200'}`}
              >
                <div>
                  <p className={`font-medium ${textColor} truncate`}>
                    {backlink.referring_domain}
                  </p>
                  <p className="text-sm text-gray-500">
                    {new Date(backlink.timestamp).toLocaleDateString()}
                  </p>
                </div>
                <Badge variant={getAuthorityBadgeColor(backlink.authority_score)}>
                  {backlink.authority_score.toFixed(1)}
                </Badge>
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
