'use client';

import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useTheme } from 'next-themes';
import axios from 'axios';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Button } from '@/components/ui/button';

interface RankHistoryData {
  id: string;
  keyword_id: string;
  rank: number | null;
  search_volume: number | null;
  cpc: number | null;
  device: string;
  location: string | null;
  timestamp: string;
}

interface RankHistoryChartProps {
  projectId: string;
  keywordId?: string;
  device?: string;
}

export function RankHistoryChart({
  projectId,
  keywordId,
  device,
}: RankHistoryChartProps) {
  const { theme } = useTheme();
  const [timeRange, setTimeRange] = useState<'6mo' | '1yr'>('6mo');

  const days = timeRange === '6mo' ? 180 : 365;

  // Fetch rank history data
  const { data: historyData, isLoading, error } = useQuery({
    queryKey: ['rankHistory', projectId, keywordId, device, days],
    queryFn: async () => {
      const params = new URLSearchParams({
        days: days.toString(),
        limit: '500',
      });

      if (keywordId) params.append('keyword_id', keywordId);
      if (device) params.append('device', device);

      const response = await axios.get(
        `/api/seo/projects/${projectId}/keywords/history?${params}`
      );
      return response.data.data as RankHistoryData[];
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Process data for chart
  const chartData = useMemo(() => {
    if (!historyData) return [];

    // Group by timestamp and calculate average rank
    const grouped = historyData.reduce(
      (acc, item) => {
        const date = new Date(item.timestamp).toLocaleDateString();
        if (!acc[date]) {
          acc[date] = { date, ranks: [], volumes: [], cpcs: [] };
        }
        if (item.rank) acc[date].ranks.push(item.rank);
        if (item.search_volume) acc[date].volumes.push(item.search_volume);
        if (item.cpc) acc[date].cpcs.push(item.cpc);
        return acc;
      },
      {} as Record<
        string,
        { date: string; ranks: number[]; volumes: number[]; cpcs: number[] }
      >
    );

    // Convert to chart format
    return Object.entries(grouped).map(([_, data]) => ({
      date: data.date,
      rank:
        data.ranks.length > 0
          ? Math.round(data.ranks.reduce((a, b) => a + b) / data.ranks.length)
          : null,
      volume:
        data.volumes.length > 0
          ? Math.round(
              data.volumes.reduce((a, b) => a + b) / data.volumes.length
            )
          : null,
      cpc:
        data.cpcs.length > 0
          ? Number(
              (data.cpcs.reduce((a, b) => a + b) / data.cpcs.length).toFixed(2)
            )
          : null,
    }));
  }, [historyData]);

  const isDark = theme === 'dark';
  const gridColor = isDark ? '#374151' : '#e5e7eb';
  const textColor = isDark ? '#e5e7eb' : '#1f2937';

  if (error) {
    return (
      <div className="flex items-center justify-center h-96 text-red-500">
        Failed to load rank history
      </div>
    );
  }

  return (
    <div className="w-full space-y-4">
      <div className="flex gap-2">
        <Button
          onClick={() => setTimeRange('6mo')}
          variant={timeRange === '6mo' ? 'default' : 'outline'}
          size="sm"
        >
          Last 6 Months
        </Button>
        <Button
          onClick={() => setTimeRange('1yr')}
          variant={timeRange === '1yr' ? 'default' : 'outline'}
          size="sm"
        >
          Last Year
        </Button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-96">
          <div className="text-gray-500">Loading rank history...</div>
        </div>
      ) : chartData.length === 0 ? (
        <div className="flex items-center justify-center h-96">
          <div className="text-gray-500">No rank history data available</div>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={400}>
          <LineChart
            data={chartData}
            margin={{ top: 5, right: 30, left: 0, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
            <XAxis
              dataKey="date"
              stroke={textColor}
              style={{ fontSize: '12px' }}
            />
            <YAxis
              yAxisId="left"
              stroke={textColor}
              label={{ value: 'Rank Position', angle: -90, position: 'insideLeft' }}
              style={{ fontSize: '12px' }}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              stroke={textColor}
              label={{ value: 'Volume / CPC', angle: 90, position: 'insideRight' }}
              style={{ fontSize: '12px' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: isDark ? '#1f2937' : '#ffffff',
                border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
                color: textColor,
              }}
            />
            <Legend />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="rank"
              stroke="#ef4444"
              dot={false}
              isAnimationActive={false}
              name="Average Rank"
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="volume"
              stroke="#3b82f6"
              dot={false}
              isAnimationActive={false}
              name="Search Volume"
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="cpc"
              stroke="#10b981"
              dot={false}
              isAnimationActive={false}
              name="CPC"
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
