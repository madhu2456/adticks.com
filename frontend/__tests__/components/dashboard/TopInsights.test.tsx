import React from "react";
import { render, screen } from "@testing-library/react";
import { TopInsights } from "@/components/dashboard/TopInsights";
import { Insight } from "@/lib/types";

// Mock next/link since it's used inside the component
jest.mock("next/link", () => {
  return ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  );
});

const mockInsights: Insight[] = [
  {
    id: "1",
    title: "Improve title tags for high-volume keywords",
    description: "Your title tags are missing primary keywords on 12 pages.",
    category: "seo",
    priority: "P1",
    data_snippet: "12 pages affected",
    action_label: "View Pages",
    action_url: "/seo",
    created_at: new Date().toISOString(),
    is_read: false,
  },
  {
    id: "2",
    title: "AI visibility dropping in ChatGPT",
    description: "Your brand was mentioned in only 3 out of 20 AI prompts.",
    category: "ai",
    priority: "P2",
    created_at: new Date().toISOString(),
    is_read: false,
  },
  {
    id: "3",
    title: "GSC impressions down 15%",
    description: "Search impressions have decreased significantly this week.",
    category: "gsc",
    priority: "P3",
    created_at: new Date().toISOString(),
    is_read: true,
  },
];

describe("TopInsights", () => {
  it("renders the Top Insights card title", () => {
    render(<TopInsights insights={mockInsights} />);
    expect(screen.getByText("Top Insights")).toBeInTheDocument();
  });

  it("renders insight titles", () => {
    render(<TopInsights insights={mockInsights} />);
    expect(screen.getByText("Improve title tags for high-volume keywords")).toBeInTheDocument();
    expect(screen.getByText("AI visibility dropping in ChatGPT")).toBeInTheDocument();
    expect(screen.getByText("GSC impressions down 15%")).toBeInTheDocument();
  });

  it("renders insight descriptions", () => {
    render(<TopInsights insights={mockInsights} />);
    expect(screen.getByText(/title tags are missing primary keywords/i)).toBeInTheDocument();
  });

  it("renders priority badges", () => {
    render(<TopInsights insights={mockInsights} />);
    expect(screen.getByText(/P1\s*·/)).toBeInTheDocument();
    expect(screen.getByText(/P2\s*·/)).toBeInTheDocument();
    expect(screen.getByText(/P3\s*·/)).toBeInTheDocument();
  });

  it("renders category badges", () => {
    render(<TopInsights insights={mockInsights} />);
    expect(screen.getByText("seo")).toBeInTheDocument();
    expect(screen.getByText("ai")).toBeInTheDocument();
    expect(screen.getByText("gsc")).toBeInTheDocument();
  });

  it("renders data_snippet when provided", () => {
    render(<TopInsights insights={mockInsights} />);
    expect(screen.getByText("12 pages affected")).toBeInTheDocument();
  });

  it("renders action link when action_label is provided", () => {
    render(<TopInsights insights={mockInsights} />);
    expect(screen.getByText("View Pages")).toBeInTheDocument();
  });

  it("renders at most 3 insights", () => {
    const manyInsights: Insight[] = Array.from({ length: 10 }, (_, i) => ({
      id: String(i),
      title: `Insight ${i}`,
      description: `Description ${i}`,
      category: "seo" as const,
      priority: "P3" as const,
      created_at: new Date().toISOString(),
      is_read: false,
    }));
    render(<TopInsights insights={manyInsights} />);
    // Only first 3 should be rendered
    expect(screen.getByText("Insight 0")).toBeInTheDocument();
    expect(screen.getByText("Insight 1")).toBeInTheDocument();
    expect(screen.getByText("Insight 2")).toBeInTheDocument();
    expect(screen.queryByText("Insight 3")).not.toBeInTheDocument();
  });

  it("renders empty state with no insights", () => {
    render(<TopInsights insights={[]} />);
    expect(screen.getByText("Top Insights")).toBeInTheDocument();
  });

  it("renders loading skeletons when loading is true", () => {
    render(<TopInsights loading />);
    expect(screen.queryByText("Top Insights")).not.toBeInTheDocument();
  });

  it("renders View all link", () => {
    render(<TopInsights insights={mockInsights} />);
    expect(screen.getByText(/view all/i)).toBeInTheDocument();
  });
});
