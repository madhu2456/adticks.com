# Frontend Developer Guide — AdTicks

This guide covers the Next.js 14 frontend: project structure, pages, components, data hooks, the API client, the design system, and how to add new features.

---

## Table of Contents

- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Running the Frontend](#running-the-frontend)
- [Routing — App Router](#routing--app-router)
- [Pages Reference](#pages-reference)
- [Layout Architecture](#layout-architecture)
- [Design System](#design-system)
- [Component Library](#component-library)
- [Data Hooks](#data-hooks)
- [API Client](#api-client)
- [Authentication Management](#authentication-management)
- [TypeScript Types](#typescript-types)
- [Mock Data & Graceful Degradation](#mock-data--graceful-degradation)
- [Charts](#charts)
- [Adding a New Page — Step-by-Step](#adding-a-new-page--step-by-step)
- [Testing](#testing)
- [Environment Variables](#environment-variables)

---

## Technology Stack

| Library | Version | Purpose |
|---------|---------|---------|
| Next.js | 14.2 | React framework, App Router, SSR |
| React | 18.3 | UI rendering |
| TypeScript | 5.5 | Type safety |
| Tailwind CSS | 3.4 | Utility-first styling |
| Framer Motion | 11.3 | Animations and transitions |
| Lucide React | 0.417 | Icon library (400+ icons) |
| TanStack Query | 5.51 | Server state management, caching |
| Axios | 1.7 | HTTP client with interceptors |
| Recharts | 2.12 | Composable chart components |
| Class Variance Authority | 0.7 | Component variant system (CVA) |
| Radix UI | various | Accessible headless UI primitives |
| date-fns | 3.6 | Date formatting and manipulation |
| Next Auth | 4.24 | Authentication session management |

---

## Project Structure

```
frontend/
├── app/                           # Next.js App Router
│   ├── layout.tsx                 # Root HTML wrapper, QueryProvider, dark mode
│   ├── globals.css                # Tailwind directives + CSS custom properties
│   ├── (auth)/                    # Auth route group (no dashboard shell)
│   │   ├── layout.tsx             #   Centred full-screen layout
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   └── (dashboard)/               # Dashboard route group (with Sidebar + Header)
│       ├── layout.tsx             #   Wraps children in <DashboardLayout>
│       ├── page.tsx               #   / → Overview
│       ├── seo/page.tsx           #   /seo
│       ├── aeo/page.tsx           #   /aeo
│       ├── gsc/page.tsx           #   /gsc
│       ├── ads/page.tsx           #   /ads
│       ├── insights/page.tsx      #   /insights
│       └── settings/page.tsx      #   /settings
├── components/
│   ├── layout/
│   │   ├── DashboardLayout.tsx    # Sidebar + Header + main content wrapper
│   │   ├── Sidebar.tsx            # Collapsible left navigation
│   │   └── Header.tsx             # Top bar: project switcher, scan, notifications
│   ├── ui/                        # Design system primitives
│   │   ├── button.tsx             #   Button (CVA variants: default, ghost, outline…)
│   │   ├── card.tsx               #   Card + CardHeader + CardContent + CardFooter
│   │   ├── badge.tsx              #   Status badges
│   │   ├── input.tsx              #   Form input
│   │   ├── label.tsx              #   Form label
│   │   ├── select.tsx             #   Dropdown select
│   │   ├── tabs.tsx               #   Tab navigation
│   │   └── skeleton.tsx           #   Loading skeleton shimmer
│   ├── dashboard/
│   │   ├── VisibilityScore.tsx    # Radial gauge + channel progress bars
│   │   ├── ChannelBreakdown.tsx   # Bar chart with period switcher
│   │   ├── TopInsights.tsx        # Priority insight cards grid
│   │   └── RecentActivity.tsx     # Timeline activity feed
│   ├── seo/
│   │   ├── KeywordTable.tsx       # Searchable keyword rankings table
│   │   ├── RankTracker.tsx        # Position history line chart
│   │   ├── OnPageScore.tsx        # Audit checklist
│   │   ├── ContentGaps.tsx        # Opportunity topics list
│   │   └── TechnicalSEO.tsx       # Technical check results
│   ├── ai/
│   │   ├── SOVChart.tsx           # Share of Voice pie/bar chart
│   │   ├── PromptResults.tsx      # LLM response table
│   │   ├── CompetitorComparison.tsx
│   │   └── MentionHeatmap.tsx
│   ├── gsc/
│   │   ├── ImpressionsChart.tsx
│   │   ├── CTRChart.tsx
│   │   └── QueryTable.tsx
│   ├── ads/
│   │   ├── PerformanceChart.tsx
│   │   └── CampaignTable.tsx
│   ├── charts/                    # Recharts wrappers (shared)
│   │   ├── LineChart.tsx
│   │   ├── BarChart.tsx
│   │   ├── RadialChart.tsx
│   │   └── HeatmapChart.tsx
│   └── providers/
│       └── QueryProvider.tsx      # React Query provider wrapper
├── hooks/                         # React Query data hooks
│   ├── useProject.ts
│   ├── useSEO.ts
│   ├── useAIVisibility.ts
│   ├── useGSC.ts
│   ├── useAds.ts
│   └── useInsights.ts
├── lib/
│   ├── types.ts                   # All TypeScript interfaces
│   ├── api.ts                     # Axios client + endpoint map
│   ├── auth.ts                    # JWT localStorage helpers
│   ├── utils.ts                   # Number/date/color formatting
│   └── mockData.ts                # Offline fallback data
└── __tests__/                     # Jest test files
```

---

## Running the Frontend

```bash
# Inside Docker (recommended)
docker-compose up -d frontend

# Locally with hot reload
cd frontend
npm install
npm run dev        # http://localhost:3002

# Production build
npm run build
npm start

# Type check
npm run type-check

# Lint
npm run lint
```

---

## Routing — App Router

AdTicks uses Next.js 14 **App Router** with two route groups:

| Group | Layout | Purpose |
|-------|--------|---------|
| `(auth)` | Centred form | Login, Register — no navigation chrome |
| `(dashboard)` | Sidebar + Header | All authenticated dashboard pages |

Route groups use parentheses to avoid affecting the URL path. `(dashboard)/page.tsx` maps to `/`, not `/dashboard`.

### Protected routes

All dashboard pages require authentication. The DashboardLayout reads the JWT token from localStorage. If the token is missing or expired, the Axios interceptor catches the 401 and redirects to `/login`.

---

## Pages Reference

### `/` — Overview Dashboard (`app/(dashboard)/page.tsx`)

The main landing page after login. Displays:
- Time-based greeting ("Good morning, Madhu 👋")
- Quick action shortcuts (SEO Report, AI Scan, GSC Insights, Campaign Perf.)
- 4 stat cards with sparkline charts (Keywords, AI Mentions, GSC Impressions, Ad Spend)
- `VisibilityScore` widget with animated gauge
- `ChannelBreakdown` bar chart with period switcher
- `RecentActivity` timeline feed
- `TopInsights` priority recommendation cards

Data source: `mockData.ts` (with React Query fallback to API)

### `/seo` — SEO Hub (`app/(dashboard)/seo/page.tsx`)

Tabbed interface:
- **Keywords** — Searchable table with keyword, intent badge, difficulty, volume, position, trend
- **Rankings** — Position history line chart per keyword
- **On-Page** — Audit checklist (pass/warning/fail with fix suggestions)
- **Content Gaps** — Topic opportunities with volume, difficulty, competitor coverage
- **Technical** — HTTPS, sitemap, Core Web Vitals, crawl errors

### `/aeo` — AEO Hub (`app/(dashboard)/aeo/page.tsx`)

- AEO Dashboard with composite score
- LLM Visibility tracker (ChatGPT, Claude, Perplexity)
- Snippet & PAA (People Also Ask) history
- AI Content Recommendations
- FAQ Generator from PAA questions

### `/gsc` — Search Console (`app/(dashboard)/gsc/page.tsx`)

- GSC connection status + "Connect Google Account" button
- Impressions and clicks over 28 days (line chart)
- CTR and position trend charts
- Top queries table sorted by clicks

### `/ads` — Google Ads (`app/(dashboard)/ads/page.tsx`)

- Campaign cards (name, type, status, budget, ROAS)
- Spend / impressions / clicks / conversions chart (line, 30d)
- Campaign performance table with sortable columns

### `/insights` — Insights (`app/(dashboard)/insights/page.tsx`)

- Priority filter tabs (All / P1 / P2 / P3)
- Category filter (SEO / AI / GSC / Ads / Cross-channel)
- Insight cards with: priority badge, category, description, data snippet, CTA
- Mark-as-read functionality

### `/settings` — Settings (`app/(dashboard)/settings/page.tsx`)

- Project name, domain, industry form
- Connected integrations status (GSC: Connected/Disconnected, Ads: Connected/Disconnected)
- Competitor management
- Danger zone (delete project)

---

## Layout Architecture

```
DashboardLayout (components/layout/DashboardLayout.tsx)
├── <Sidebar collapsed={bool} onToggle={fn} />
│     Width: 60px (collapsed) | 224px (expanded)
│     Animated with Framer Motion
│     Fixed left, full height
│
├── <Header sidebarCollapsed={bool} />
│     Height: 56px (h-14)
│     Fixed top, spans from sidebar edge to right
│     Content: Project switcher | ⌘K search | Live indicator | Scan | Bell | Avatar
│
└── <main className="pt-14 pl-[224px] | pl-[60px]">
      <div className="p-6 max-w-[1440px] mx-auto">
        {children}      ← Page content goes here
      </div>
    </main>
```

The sidebar toggle state lives in `DashboardLayout` and is passed down as props. Both `Sidebar` and `Header` are exported as both default and named exports for compatibility.

---

## Design System

The design system is entirely custom — built with Tailwind CSS and CSS custom properties.

### Color tokens (CSS variables in `globals.css`)

```css
:root {
  --bg:          #09090b;   /* Page background */
  --surface-1:   #0e0e10;   /* Sidebar */
  --surface-2:   #141416;   /* Cards */
  --surface-3:   #1f1f23;   /* Hover states */
  --primary:     #6366f1;   /* Indigo — brand color */
  --violet:      #8b5cf6;   /* Secondary accent */
  --pink:        #ec4899;   /* Tertiary accent */
  --success:     #22c55e;   /* Positive / up trends */
  --warning:     #eab308;   /* Alerts / trial badge */
  --danger:      #ef4444;   /* Errors / P1 priority */
  --text-1:      #fafafa;   /* Primary text */
  --text-2:      #a1a1aa;   /* Secondary text */
  --text-3:      #52525b;   /* Tertiary / labels */
}
```

### Tailwind color aliases

These map CSS variables to Tailwind classes:

```
bg-surface-2        → background: #141416
text-text-1         → color: #fafafa
text-text-2         → color: #a1a1aa
bg-primary          → background: #6366f1
text-success        → color: #22c55e
```

### Utility classes (in `globals.css`)

| Class | Effect |
|-------|--------|
| `.gradient-text` | Indigo → violet gradient text |
| `.gradient-text-pink` | Violet → pink gradient text |
| `.glass` | rgba(255,255,255,0.03) + blur(12px) |
| `.glow-primary` | box-shadow: 0 0 20px rgba(99,102,241,0.25) |
| `.dot-grid` | Subtle dot pattern background |
| `.skeleton` | Shimmer loading animation |
| `.live-dot` | Animated pulsing green dot |
| `.custom-scroll` | Styled 4px scrollbar |
| `[data-animate-in]` | Staggered page entry animation |

### Gradient border

Cards can use a gradient border via the `.gb` class:

```html
<div class="gb rounded-xl bg-surface-2 p-4">...</div>
```

This uses a CSS mask + pseudo-element approach for a clean gradient border without extra DOM elements.

### Animation patterns

- `data-animate-in="1"` through `data-animate-in="5"` — staggered slide-up on page load
- Framer Motion `AnimatePresence` — sidebar collapse, dropdown open/close
- CSS `@keyframes orbFloat` — background orb floating

---

## Component Library

### Button (`components/ui/button.tsx`)

Uses CVA for variant management:

```tsx
import { Button } from "@/components/ui/button";

<Button variant="default" size="md">Save changes</Button>
<Button variant="ghost" size="sm">Cancel</Button>
<Button variant="danger" loading>Deleting...</Button>
```

**Variants:** `default` (gradient), `secondary`, `ghost`, `outline`, `danger`, `success`, `link`
**Sizes:** `sm`, `md`, `lg`, `icon`

### Card (`components/ui/card.tsx`)

```tsx
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

<Card variant="default">
  <CardHeader>
    <CardTitle>Visibility Score</CardTitle>
  </CardHeader>
  <CardContent>
    {/* ... */}
  </CardContent>
</Card>
```

**Variants:** `default`, `glass`, `gradient`, `interactive`, `flat`

### Badge (`components/ui/badge.tsx`)

```tsx
import { Badge } from "@/components/ui/badge";

<Badge variant="p1">P1</Badge>       {/* red */}
<Badge variant="p2">P2</Badge>       {/* amber */}
<Badge variant="p3">P3</Badge>       {/* green */}
<Badge variant="secondary">SEO</Badge>
```

### Skeleton (`components/ui/skeleton.tsx`)

```tsx
import { Skeleton } from "@/components/ui/skeleton";

<Skeleton className="h-5 w-40" />     {/* shimmer loading block */}
```

### Tabs (`components/ui/tabs.tsx`)

```tsx
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";

<Tabs defaultValue="keywords">
  <TabsList>
    <TabsTrigger value="keywords">Keywords</TabsTrigger>
    <TabsTrigger value="rankings">Rankings</TabsTrigger>
  </TabsList>
  <TabsContent value="keywords"><KeywordTable /></TabsContent>
  <TabsContent value="rankings"><RankTracker /></TabsContent>
</Tabs>
```

---

## Data Hooks

All data fetching goes through React Query hooks in `hooks/`. They follow this pattern:

```typescript
// hooks/useSEO.ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { MOCK_KEYWORDS } from "@/lib/mockData";

export function useKeywords(projectId: string) {
  return useQuery({
    queryKey: ["seo", "keywords", projectId],
    queryFn: () => api.seo.getKeywords(projectId).catch(() => MOCK_KEYWORDS),
    initialData: MOCK_KEYWORDS,
    staleTime: 5 * 60 * 1000,   // 5 minutes before re-fetch
    enabled: !!projectId,
  });
}

export function useTriggerSEOAudit() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (projectId: string) => api.seo.triggerAudit(projectId),
    onSuccess: (_, projectId) => {
      queryClient.invalidateQueries({ queryKey: ["seo", projectId] });
    },
  });
}
```

**Hook index:**

| Hook | Returns | Data source |
|------|---------|-------------|
| `useProjects()` | Project[] | `GET /api/projects` |
| `useActiveProject()` | Project | localStorage + `GET /api/projects/{id}` |
| `useScore(projectId)` | VisibilityScore | `GET /api/scores/{id}` |
| `useKeywords(projectId)` | Keyword[] | `GET /api/seo/rankings/{id}` |
| `useContentGaps(projectId)` | ContentGap[] | `GET /api/seo/gaps/{id}` |
| `useTechnicalSEO(projectId)` | TechnicalCheck[] | `GET /api/seo/technical/{id}` |
| `useAIScore(projectId)` | AIScore | `GET /api/scores/{id}` (AI component) |
| `useAIScan(projectId)` | AIPromptResult[] | `GET /api/results/{id}` |
| `useGSCQueries(projectId)` | GSCQuery[] | `GET /api/gsc/queries/{id}` |
| `useAdsPerformance(projectId)` | AdsPerformance | `GET /api/ads/performance/{id}` |
| `useInsights(projectId)` | Insight[] | `GET /api/insights/{id}` |

---

## API Client

`lib/api.ts` is a typed Axios wrapper:

```typescript
import axios from "axios";
import { getAccessToken, clearTokens } from "./auth";

const client = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: { "Content-Type": "application/json" },
});

// Attach JWT token to every request
client.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Handle 401 — clear tokens and redirect
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearTokens();
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// Namespace by domain
export const api = {
  auth: {
    login:    (body) => client.post("/auth/login", body).then(r => r.data),
    register: (body) => client.post("/auth/register", body).then(r => r.data),
    me:       ()     => client.get("/auth/me").then(r => r.data),
  },
  projects: {
    list:   ()   => client.get("/projects").then(r => r.data),
    create: (b)  => client.post("/projects", b).then(r => r.data),
    update: (id, b) => client.put(`/projects/${id}`, b).then(r => r.data),
    delete: (id) => client.delete(`/projects/${id}`),
  },
  seo: {
    getKeywords:  (pid) => client.get(`/seo/rankings/${pid}`).then(r => r.data),
    getGaps:      (pid) => client.get(`/seo/gaps/${pid}`).then(r => r.data),
    getTechnical: (pid) => client.get(`/seo/technical/${pid}`).then(r => r.data),
    triggerAudit: (pid) => client.post("/seo/audit", { project_id: pid }).then(r => r.data),
  },
  // ... ai, gsc, ads, insights
};
```

---

## Authentication Management

`lib/auth.ts` manages JWT tokens in localStorage:

```typescript
const KEYS = {
  ACCESS:  "adticks_access_token",
  REFRESH: "adticks_refresh_token",
  USER:    "adticks_user",
};

export function setTokens(access: string, refresh?: string) {
  localStorage.setItem(KEYS.ACCESS, access);
  if (refresh) localStorage.setItem(KEYS.REFRESH, refresh);
}

export function getAccessToken(): string | null {
  return localStorage.getItem(KEYS.ACCESS);
}

export function clearTokens() {
  Object.values(KEYS).forEach(k => localStorage.removeItem(k));
}

export function isAuthenticated(): boolean {
  return !!getAccessToken();
}

export function getTrialDaysLeft(): number {
  const user = getUser();
  if (!user?.trial_ends_at) return 0;
  const msLeft = new Date(user.trial_ends_at).getTime() - Date.now();
  return Math.max(0, Math.ceil(msLeft / (1000 * 60 * 60 * 24)));
}
```

---

## TypeScript Types

All shared types are in `lib/types.ts`. Key interfaces:

```typescript
interface VisibilityScore {
  overall: number;   // 0-100 composite
  seo:     number;
  ai:      number;
  gsc:     number;
  ads:     number;
  computed_at: string;
}

interface Keyword {
  id: string;
  keyword: string;
  intent: "informational" | "navigational" | "transactional" | "commercial";
  difficulty: number;   // 0-100
  volume: number;       // monthly searches
  position: number;     // current SERP rank
  position_change: number;
  url: string;
}

interface Insight {
  id: string;
  title: string;
  description: string;
  category: "seo" | "ai" | "gsc" | "ads" | "cross-channel";
  priority: "P1" | "P2" | "P3";
  data_snippet?: string;   // code/metric callout
  action_label?: string;
  action_url?: string;
  created_at: string;
  is_read: boolean;
}

interface AdCampaign {
  id: string;
  name: string;
  status: "ENABLED" | "PAUSED" | "REMOVED";
  daily_budget_usd: number;
  bid_strategy: string;
  target_roas: number;
  clicks: number;
  impressions: number;
  conversions: number;
  spend_usd: number;
  roas: number;
  ctr: number;
}
```

---

## Mock Data & Graceful Degradation

`lib/mockData.ts` provides fallback data for every hook. This means:
1. The dashboard looks fully populated even before the API responds
2. The app works completely without a running backend (demo mode)
3. Loading states are minimised on first paint

Pattern:

```typescript
// In the hook
queryFn: () => api.seo.getKeywords(projectId).catch(() => MOCK_KEYWORDS),
initialData: MOCK_KEYWORDS,
```

If the API call fails for any reason (network error, 401, 500), the mock data is displayed and the hook silently falls back.

---

## Charts

All charts use **Recharts** wrapped in thin components under `components/charts/`.

```tsx
import { LineChart } from "@/components/charts/LineChart";

<LineChart
  data={data}
  xKey="date"
  lines={[
    { key: "clicks",      name: "Clicks",      color: "#6366f1" },
    { key: "impressions", name: "Impressions",  color: "#8b5cf6" },
  ]}
  height={240}
/>
```

Recharts is globally styled via `globals.css` `.recharts-*` selectors to match the dark theme (no grid lines, dark text, custom tooltip).

Custom tooltip pattern:

```tsx
const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="recharts-custom-tooltip">
      <p className="text-[11px] text-text-3 mb-2">{label}</p>
      {payload.map(p => (
        <p key={p.name} className="text-[13px] font-semibold" style={{ color: p.color }}>
          {p.name}: {p.value}
        </p>
      ))}
    </div>
  );
};
```

---

## Adding a New Page — Step-by-Step

Example: adding a `/reports` page.

### 1. Create the page file

```tsx
// app/(dashboard)/reports/page.tsx
"use client";
import React from "react";

export default function ReportsPage() {
  return (
    <div className="space-y-6">
      <div data-animate-in="1">
        <h1 className="text-[22px] font-bold text-text-1">Reports</h1>
        <p className="text-[13px] text-text-3 mt-1">Export and schedule automated reports</p>
      </div>
      {/* Your components here */}
    </div>
  );
}
```

### 2. Add to the sidebar navigation

In `components/layout/Sidebar.tsx`, add to the relevant `NAV_SECTIONS` array:

```tsx
{
  label: "Reports",
  href: "/reports",
  icon: FileText,
  shortcut: "G R",
  description: "Export data",
},
```

### 3. Create a data hook (if needed)

```typescript
// hooks/useReports.ts
export function useReports(projectId: string) {
  return useQuery({
    queryKey: ["reports", projectId],
    queryFn: () => api.reports.list(projectId).catch(() => MOCK_REPORTS),
    initialData: MOCK_REPORTS,
    staleTime: 10 * 60 * 1000,
  });
}
```

### 4. Add API endpoint to the client

```typescript
// lib/api.ts — inside the api object
reports: {
  list:     (pid) => client.get(`/reports/${pid}`).then(r => r.data),
  generate: (pid, config) => client.post(`/reports/generate`, { project_id: pid, ...config }).then(r => r.data),
},
```

### 5. Add TypeScript types

```typescript
// lib/types.ts
interface Report {
  id: string;
  project_id: string;
  type: "seo" | "ai" | "full";
  format: "pdf" | "csv";
  created_at: string;
  url: string;
}
```

### 6. Add mock data

```typescript
// lib/mockData.ts
export const MOCK_REPORTS: Report[] = [
  { id: "1", project_id: "demo", type: "full", format: "pdf", created_at: "...", url: "#" },
];
```

### 7. Write tests

```typescript
// __tests__/reports.test.tsx
import { render, screen } from "@testing-library/react";
import ReportsPage from "@/app/(dashboard)/reports/page";

test("renders reports page heading", () => {
  render(<ReportsPage />);
  expect(screen.getByText("Reports")).toBeInTheDocument();
});
```

---

## Testing

Tests use **Jest** + **@testing-library/react**.

```bash
# Run all tests
npm test

# Watch mode
npm run test:watch

# Coverage report
npm run test:coverage
```

Test files live in `__tests__/` with `*.test.tsx` naming.

**jest.config.ts** key settings:

```typescript
{
  testEnvironment: "jsdom",
  setupFilesAfterFramework: ["<rootDir>/jest.setup.ts"],
  moduleNameMapper: { "^@/(.*)$": "<rootDir>/$1" },  // resolve @/ alias
}
```

**jest.setup.ts** imports `@testing-library/jest-dom` for DOM matchers like `toBeInTheDocument()`.

---

## Environment Variables

```bash
# Required
NEXT_PUBLIC_API_URL=http://localhost:8002/api   # Backend API URL
NEXTAUTH_SECRET=your-secret-here               # NextAuth signing secret
NEXTAUTH_URL=http://localhost:3002             # Canonical app URL

# Optional (for Google OAuth in frontend)
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
```

Variables prefixed with `NEXT_PUBLIC_` are exposed to the browser. All others are server-only.
