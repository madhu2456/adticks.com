import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import axios from 'axios';
import { RankHistoryChart } from '@/components/seo/RankHistoryChart';
import { CompetitorAnalysis } from '@/components/seo/CompetitorAnalysis';
import { BacklinkDashboard } from '@/components/seo/BacklinkDashboard';

jest.mock('axios', () => {
  const mockAxios = {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
    patch: jest.fn(),
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() },
    },
    create: jest.fn(),
  };
  mockAxios.create.mockReturnValue(mockAxios);
  return mockAxios;
});
jest.mock('next-themes', () => ({
  useTheme: jest.fn(() => ({ theme: 'light', setTheme: jest.fn() })),
}));

jest.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: any) => <div>{children}</div>,
  LineChart: ({ children }: any) => <div>{children}</div>,
  Line: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  Legend: () => null,
}));

const mockAxios = axios as jest.Mocked<typeof axios>;
const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
});

// ============================================================================
// RankHistoryChart Tests
// ============================================================================
describe('RankHistoryChart', () => {
  const projectId = '550e8400-e29b-41d4-a716-446655440000';
  const mockRankData = {
    data: [
      {
        id: '1',
        keyword_id: 'kw1',
        rank: 5,
        search_volume: 2400,
        cpc: 5.5,
        device: 'desktop',
        location: 'US',
        timestamp: new Date().toISOString(),
      },
    ],
    total: 1,
    skip: 0,
    limit: 50,
    has_more: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    queryClient.clear();
  });

  test('renders rank history chart with time range buttons', async () => {
    mockAxios.get.mockResolvedValueOnce({ data: mockRankData });

    render(
      <QueryClientProvider client={queryClient}>
        <RankHistoryChart projectId={projectId} />
      </QueryClientProvider>
    );

    expect(screen.getByText(/Last 6 Months/i)).toBeInTheDocument();
    expect(screen.getByText(/Last Year/i)).toBeInTheDocument();
  });

  test('loads rank history data on mount', async () => {
    mockAxios.get.mockResolvedValueOnce({ data: mockRankData });

    render(
      <QueryClientProvider client={queryClient}>
        <RankHistoryChart projectId={projectId} />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(mockAxios.get).toHaveBeenCalledWith(
        expect.stringContaining(`/seo/projects/${projectId}/keywords/history`)
      );
    });
  });

  test('handles error gracefully', async () => {
    mockAxios.get.mockRejectedValueOnce(new Error('API Error'));

    render(
      <QueryClientProvider client={queryClient}>
        <RankHistoryChart projectId={projectId} />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/Failed to load rank history/i)).toBeInTheDocument();
    });
  });

  test('changes time range when button clicked', async () => {
    mockAxios.get.mockResolvedValueOnce({ data: mockRankData });

    render(
      <QueryClientProvider client={queryClient}>
        <RankHistoryChart projectId={projectId} />
      </QueryClientProvider>
    );

    const yearButton = await waitFor(() => screen.getByText(/Last Year/i));
    await userEvent.click(yearButton);

    await waitFor(() => {
      expect(mockAxios.get).toHaveBeenCalledWith(
        expect.stringContaining('days=365')
      );
    });
  });

  test('includes device filter when provided', async () => {
    mockAxios.get.mockResolvedValueOnce({ data: mockRankData });

    render(
      <QueryClientProvider client={queryClient}>
        <RankHistoryChart projectId={projectId} device="mobile" />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(mockAxios.get).toHaveBeenCalledWith(
        expect.stringContaining('device=mobile')
      );
    });
  });
});

// ============================================================================
// CompetitorAnalysis Tests
// ============================================================================
describe('CompetitorAnalysis', () => {
  const projectId = '550e8400-e29b-41d4-a716-446655440001';
  const mockCompetitorData = {
    data: [
      {
        id: '1',
        project_id: projectId,
        competitor_domain: 'competitor1.com',
        keywords: ['keyword1', 'keyword2', 'keyword3'],
        count: 3,
        timestamp: new Date().toISOString(),
      },
    ],
    total: 1,
    skip: 0,
    limit: 10,
    has_more: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    queryClient.clear();
  });

  test('renders competitor analysis component', async () => {
    mockAxios.get.mockResolvedValueOnce({ data: mockCompetitorData });

    render(
      <QueryClientProvider client={queryClient}>
        <CompetitorAnalysis projectId={projectId} />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/Competitor Keywords Analysis/i)).toBeInTheDocument();
    });
  });

  test('displays competitor domains', async () => {
    mockAxios.get.mockResolvedValueOnce({ data: mockCompetitorData });

    render(
      <QueryClientProvider client={queryClient}>
        <CompetitorAnalysis projectId={projectId} />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('competitor1.com')).toBeInTheDocument();
    });
  });

  test('shows total competitor count', async () => {
    mockAxios.get.mockResolvedValueOnce({ data: mockCompetitorData });

    render(
      <QueryClientProvider client={queryClient}>
        <CompetitorAnalysis projectId={projectId} />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/Total competitors: 1/i)).toBeInTheDocument();
    });
  });

  test('expands competitor details on Show click', async () => {
    mockAxios.get.mockResolvedValueOnce({ data: mockCompetitorData });

    render(
      <QueryClientProvider client={queryClient}>
        <CompetitorAnalysis projectId={projectId} />
      </QueryClientProvider>
    );

    const showButton = await waitFor(() => screen.getByText(/Show/i));
    await userEvent.click(showButton);

    await waitFor(() => {
      expect(screen.getByText(/keyword1/i)).toBeInTheDocument();
    });
  });

  test('handles empty data state', async () => {
    mockAxios.get.mockResolvedValueOnce({
      data: { ...mockCompetitorData, data: [], total: 0 },
    });

    render(
      <QueryClientProvider client={queryClient}>
        <CompetitorAnalysis projectId={projectId} />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/No competitor data available/i)).toBeInTheDocument();
    });
  });

  test('disables next button on last page', async () => {
    mockAxios.get.mockResolvedValueOnce({ data: mockCompetitorData });

    render(
      <QueryClientProvider client={queryClient}>
        <CompetitorAnalysis projectId={projectId} pageSize={10} />
      </QueryClientProvider>
    );

    const nextButton = await waitFor(() => screen.getByText(/Next/i));
    expect(nextButton).toBeDisabled();
  });
});

// ============================================================================
// BacklinkDashboard Tests
// ============================================================================
describe('BacklinkDashboard', () => {
  const projectId = '550e8400-e29b-41d4-a716-446655440002';
  const mockBacklinkData = {
    data: [
      {
        id: '1',
        project_id: projectId,
        referring_domain: 'domain1.com',
        authority_score: 85,
        timestamp: new Date().toISOString(),
      },
      {
        id: '2',
        project_id: projectId,
        referring_domain: 'domain2.com',
        authority_score: 45,
        timestamp: new Date().toISOString(),
      },
    ],
    total: 2,
    skip: 0,
    limit: 15,
    has_more: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    queryClient.clear();
  });

  test('renders backlink dashboard', async () => {
    mockAxios.get.mockResolvedValueOnce({ data: mockBacklinkData });

    render(
      <QueryClientProvider client={queryClient}>
        <BacklinkDashboard projectId={projectId} />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/Backlinks Overview/i)).toBeInTheDocument();
    });
  });

  test('displays backlink statistics', async () => {
    mockAxios.get.mockResolvedValueOnce({ data: mockBacklinkData });

    render(
      <QueryClientProvider client={queryClient}>
        <BacklinkDashboard projectId={projectId} />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/Total Backlinks/i)).toBeInTheDocument();
      expect(screen.getByText(/Avg Authority/i)).toBeInTheDocument();
    });
  });

  test('displays referring domains', async () => {
    mockAxios.get.mockResolvedValueOnce({ data: mockBacklinkData });

    render(
      <QueryClientProvider client={queryClient}>
        <BacklinkDashboard projectId={projectId} />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('domain1.com')).toBeInTheDocument();
      expect(screen.getByText('domain2.com')).toBeInTheDocument();
    });
  });

  test('filters by minimum authority', async () => {
    mockAxios.get.mockResolvedValueOnce({
      data: {
        data: [mockBacklinkData.data[0]],
        total: 1,
        skip: 0,
        limit: 15,
        has_more: false,
      },
    });

    render(
      <QueryClientProvider client={queryClient}>
        <BacklinkDashboard projectId={projectId} />
      </QueryClientProvider>
    );

    const input = await waitFor(() =>
      screen.getByPlaceholderText(/Filter by min authority/i)
    );

    await userEvent.type(input, '70');

    await waitFor(() => {
      expect(mockAxios.get).toHaveBeenCalledWith(
        expect.stringContaining('min_authority=70')
      );
    });
  });

  test('clears authority filter', async () => {
    mockAxios.get.mockResolvedValueOnce({ data: mockBacklinkData });

    render(
      <QueryClientProvider client={queryClient}>
        <BacklinkDashboard projectId={projectId} />
      </QueryClientProvider>
    );

    const clearButton = await waitFor(() => screen.getByText(/Clear/i));
    await userEvent.click(clearButton);

    const input = screen.getByPlaceholderText(/Filter by min authority/i);
    expect(input).toHaveValue(null);
  });

  test('handles pagination', async () => {
    mockAxios.get.mockImplementation((url: string) => {
      if (url.includes('/backlinks/stats')) {
        return Promise.resolve({ data: { total_backlinks: 30, avg_authority: 50 } });
      }
      if (url.includes('/backlinks/intersect')) {
        return Promise.resolve({ data: [] });
      }
      if (url.includes('/backlinks')) {
        return Promise.resolve({
          data: {
            ...mockBacklinkData,
            total: 30,
            has_more: true,
          },
        });
      }
      return Promise.resolve({ data: {} });
    });

    render(
      <QueryClientProvider client={queryClient}>
        <BacklinkDashboard projectId={projectId} />
      </QueryClientProvider>
    );

    await waitFor(() => {
      const nextButton = screen.getByText(/Next/i);
      expect(nextButton).not.toBeDisabled();
    });

    const nextButton = screen.getByText(/Next/i);
    await userEvent.click(nextButton);

    await waitFor(() => {
      expect(mockAxios.get).toHaveBeenCalledWith(
        expect.stringContaining('skip=15')
      );
    });
  });

  test('disables previous button on first page', async () => {
    mockAxios.get.mockResolvedValueOnce({ data: mockBacklinkData });

    render(
      <QueryClientProvider client={queryClient}>
        <BacklinkDashboard projectId={projectId} />
      </QueryClientProvider>
    );

    const previousButton = await waitFor(() => screen.getByText(/Previous/i));
    expect(previousButton).toBeDisabled();
  });

  test('shows empty state message', async () => {
    mockAxios.get.mockResolvedValueOnce({
      data: { data: [], total: 0, skip: 0, limit: 15, has_more: false },
    });

    render(
      <QueryClientProvider client={queryClient}>
        <BacklinkDashboard projectId={projectId} />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/No backlinks available/i)).toBeInTheDocument();
    });
  });
});
