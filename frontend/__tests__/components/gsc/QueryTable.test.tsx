import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { QueryTable } from "@/components/gsc/QueryTable";

const mockData = [
  { query: "adticks seo tool", clicks: 500, impressions: 8000, ctr: 6.25, position: 2.3, positionChange: 1 },
  { query: "keyword rank tracker", clicks: 300, impressions: 5000, ctr: 3.0, position: 5.1, positionChange: -2 },
  { query: "free seo checker", clicks: 80, impressions: 10000, ctr: 0.8, position: 12.5, positionChange: 0 },
  { query: "buy seo software online", clicks: 200, impressions: 4000, ctr: 5.0, position: 3.8, positionChange: 3 },
];

describe("QueryTable", () => {
  it("renders all query rows", () => {
    render(<QueryTable data={mockData} />);
    expect(screen.getByText("adticks seo tool")).toBeInTheDocument();
    expect(screen.getByText("keyword rank tracker")).toBeInTheDocument();
    expect(screen.getByText("free seo checker")).toBeInTheDocument();
    expect(screen.getByText("buy seo software online")).toBeInTheDocument();
  });

  it("renders default title 'Top Queries'", () => {
    render(<QueryTable data={mockData} />);
    expect(screen.getByText("Top Queries")).toBeInTheDocument();
  });

  it("renders custom title when provided", () => {
    render(<QueryTable data={mockData} title="My Queries" />);
    expect(screen.getByText("My Queries")).toBeInTheDocument();
  });

  it("filters queries when searching", () => {
    render(<QueryTable data={mockData} />);
    const input = screen.getByPlaceholderText(/filter queries/i);
    fireEvent.change(input, { target: { value: "rank" } });
    expect(screen.getByText("keyword rank tracker")).toBeInTheDocument();
    expect(screen.queryByText("adticks seo tool")).not.toBeInTheDocument();
    expect(screen.queryByText("free seo checker")).not.toBeInTheDocument();
  });

  it("shows empty message when no queries match filter", () => {
    render(<QueryTable data={mockData} />);
    const input = screen.getByPlaceholderText(/filter queries/i);
    fireEvent.change(input, { target: { value: "zzznomatch" } });
    expect(screen.getByText(/no queries match your filter/i)).toBeInTheDocument();
  });

  it("renders table column headers", () => {
    render(<QueryTable data={mockData} />);
    expect(screen.getByText("Query")).toBeInTheDocument();
    expect(screen.getByText("Clicks")).toBeInTheDocument();
    expect(screen.getByText("Impressions")).toBeInTheDocument();
    expect(screen.getByText("CTR")).toBeInTheDocument();
    expect(screen.getByText("Avg Position")).toBeInTheDocument();
  });

  it("renders CTR values as percentages", () => {
    render(<QueryTable data={mockData} />);
    expect(screen.getByText("6.3%")).toBeInTheDocument();
  });

  it("applies green color class for CTR >= 5%", () => {
    render(<QueryTable data={mockData} />);
    // 6.25% CTR badge should have green color styling
    const ctrBadge = screen.getByText("6.3%");
    expect(ctrBadge.className).toContain("10b981");
  });

  it("applies red color class for CTR < 2%", () => {
    render(<QueryTable data={mockData} />);
    // 0.8% CTR badge should have red color styling
    const ctrBadge = screen.getByText("0.8%");
    expect(ctrBadge.className).toContain("ef4444");
  });

  it("applies yellow/amber color class for CTR between 2% and 5%", () => {
    render(<QueryTable data={mockData} />);
    // 3.0% CTR badge should have amber styling
    const ctrBadge = screen.getByText("3.0%");
    expect(ctrBadge.className).toContain("f59e0b");
  });

  it("handles empty data array without crashing", () => {
    render(<QueryTable data={[]} />);
    expect(screen.getByText("Top Queries")).toBeInTheDocument();
  });

  it("renders click counts", () => {
    render(<QueryTable data={mockData} />);
    expect(screen.getByText("500")).toBeInTheDocument();
  });

  it("sorts by clicks descending by default", () => {
    render(<QueryTable data={mockData} />);
    // "adticks seo tool" has 500 clicks (highest), should appear first in tbody
    const rows = screen.getAllByRole("row");
    // rows[0] is header; rows[1] should be highest clicks
    expect(rows[1]).toHaveTextContent("adticks seo tool");
  });

  it("clicking Clicks column header toggles sort direction", () => {
    render(<QueryTable data={mockData} />);
    const clicksHeader = screen.getByText("Clicks");
    fireEvent.click(clicksHeader);
    // After clicking again (same column), sort should toggle
    const rows = screen.getAllByRole("row");
    expect(rows[1]).toHaveTextContent("free seo checker");
  });
});
