import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { InsightList } from "@/components/insights/InsightList";
import { Insight } from "@/lib/types";

const makeInsight = (id: string, overrides: Partial<Insight> = {}): Insight => ({
  id,
  title: `Insight title ${id}`,
  description: `Insight description ${id}`,
  category: "seo",
  priority: "P2",
  created_at: new Date(Date.now() - 1000 * 60 * 60 * 48).toISOString(), // old, no NEW badge
  is_read: true,
  ...overrides,
});

const mockInsights: Insight[] = [
  makeInsight("1", { title: "First insight" }),
  makeInsight("2", { title: "Second insight" }),
  makeInsight("3", { title: "Third insight" }),
];

describe("InsightList", () => {
  it("renders multiple InsightCards when data is provided", () => {
    render(<InsightList insights={mockInsights} />);
    expect(screen.getByText("First insight")).toBeInTheDocument();
    expect(screen.getByText("Second insight")).toBeInTheDocument();
    expect(screen.getByText("Third insight")).toBeInTheDocument();
  });

  it("shows skeleton/loading animation when loading is true", () => {
    const { container } = render(<InsightList insights={[]} loading />);
    // The loading state renders skeleton cards with animate-pulse
    const pulsing = container.querySelectorAll(".animate-pulse");
    expect(pulsing.length).toBeGreaterThan(0);
  });

  it("does not render insight cards in loading state", () => {
    render(<InsightList insights={mockInsights} loading />);
    expect(screen.queryByText("First insight")).not.toBeInTheDocument();
  });

  it("shows empty state message when insights array is empty", () => {
    render(<InsightList insights={[]} />);
    expect(screen.getByText("No insights found")).toBeInTheDocument();
  });

  it("shows empty state helper text", () => {
    render(<InsightList insights={[]} />);
    expect(screen.getByText(/try adjusting your filters/i)).toBeInTheDocument();
  });

  it("does not show empty state when insights are provided", () => {
    render(<InsightList insights={mockInsights} />);
    expect(screen.queryByText("No insights found")).not.toBeInTheDocument();
  });

  it("passes onMarkRead callback down to InsightCard", () => {
    const onMarkRead = jest.fn();
    const unreadInsights = [
      makeInsight("1", {
        title: "Unread insight",
        is_read: false,
        created_at: new Date(Date.now() - 1000 * 60 * 60 * 48).toISOString(),
      }),
    ];
    render(<InsightList insights={unreadInsights} onMarkRead={onMarkRead} />);
    fireEvent.click(screen.getByText(/mark as read/i));
    expect(onMarkRead).toHaveBeenCalledWith("1");
  });

  it("shows 'Load more' button when more than 10 insights exist", () => {
    const manyInsights = Array.from({ length: 15 }, (_, i) => makeInsight(String(i)));
    render(<InsightList insights={manyInsights} />);
    expect(screen.getByText(/load more/i)).toBeInTheDocument();
  });

  it("shows remaining count in 'Load more' button", () => {
    const manyInsights = Array.from({ length: 15 }, (_, i) => makeInsight(String(i)));
    render(<InsightList insights={manyInsights} />);
    expect(screen.getByText(/5 remaining/i)).toBeInTheDocument();
  });

  it("shows all insights after clicking 'Load more'", () => {
    const manyInsights = Array.from({ length: 12 }, (_, i) =>
      makeInsight(String(i), { title: `Insight ${i}` })
    );
    render(<InsightList insights={manyInsights} />);
    // Only first 10 shown initially
    expect(screen.queryByText("Insight 10")).not.toBeInTheDocument();
    fireEvent.click(screen.getByText(/load more/i));
    expect(screen.getByText("Insight 10")).toBeInTheDocument();
    expect(screen.getByText("Insight 11")).toBeInTheDocument();
  });

  it("does not show 'Load more' button for 10 or fewer insights", () => {
    render(<InsightList insights={mockInsights} />);
    expect(screen.queryByText(/load more/i)).not.toBeInTheDocument();
  });
});
