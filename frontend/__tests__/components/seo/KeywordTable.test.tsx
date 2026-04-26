import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { KeywordTable } from "@/components/seo/KeywordTable";
import { Keyword } from "@/lib/types";

const mockKeywords: Keyword[] = [
  {
    id: "1",
    keyword: "rank tracker tool",
    intent: "informational",
    difficulty: 45,
    volume: 12000,
    position: 3,
    position_change: 2,
    project_id: "proj1",
    created_at: new Date().toISOString(),
  },
  {
    id: "2",
    keyword: "buy seo software",
    intent: "transactional",
    difficulty: 72,
    volume: 8500,
    position: 8,
    position_change: -1,
    project_id: "proj1",
    created_at: new Date().toISOString(),
  },
  {
    id: "3",
    keyword: "best keyword research tools",
    intent: "commercial",
    difficulty: 60,
    volume: 22000,
    position: 5,
    position_change: 0,
    project_id: "proj1",
    created_at: new Date().toISOString(),
  },
  {
    id: "4",
    keyword: "adticks login",
    intent: "navigational",
    difficulty: 10,
    volume: 500,
    position: 1,
    position_change: 0,
    project_id: "proj1",
    created_at: new Date().toISOString(),
  },
];

describe("KeywordTable", () => {
  it("renders keyword text in the table", () => {
    render(<KeywordTable keywords={mockKeywords} onSearch={jest.fn()} />);
    expect(screen.getByText("rank tracker tool")).toBeInTheDocument();
    expect(screen.getByText("buy seo software")).toBeInTheDocument();
    expect(screen.getByText("best keyword research tools")).toBeInTheDocument();
    expect(screen.getByText("adticks login")).toBeInTheDocument();
  });

  it("renders search input", () => {
    render(<KeywordTable keywords={mockKeywords} onSearch={jest.fn()} />);
    expect(screen.getByPlaceholderText(/search keywords/i)).toBeInTheDocument();
  });

  it("filters keywords when search input changes", () => {
    render(<KeywordTable keywords={mockKeywords} onSearch={jest.fn()} />);
    const searchInput = screen.getByPlaceholderText(/search keywords/i);
    fireEvent.change(searchInput, { target: { value: "rank" } });
    expect(screen.getByText("rank tracker tool")).toBeInTheDocument();
    expect(screen.queryByText("buy seo software")).not.toBeInTheDocument();
    expect(screen.queryByText("best keyword research tools")).not.toBeInTheDocument();
  });

  it("shows no keywords message when filter matches nothing", () => {
    render(<KeywordTable keywords={mockKeywords} onSearch={jest.fn()} />);
    const searchInput = screen.getByPlaceholderText(/search keywords/i);
    fireEvent.change(searchInput, { target: { value: "zzznomatch" } });
    expect(screen.getByText(/no keywords found matching/i)).toBeInTheDocument();
  });

  it("renders intent badges", () => {
    render(<KeywordTable keywords={mockKeywords} onSearch={jest.fn()} />);
    expect(screen.getByText("informational")).toBeInTheDocument();
    expect(screen.getByText("transactional")).toBeInTheDocument();
    expect(screen.getByText("commercial")).toBeInTheDocument();
    expect(screen.getByText("navigational")).toBeInTheDocument();
  });

  it("renders table headers", () => {
    render(<KeywordTable keywords={mockKeywords} onSearch={jest.fn()} />);
    expect(screen.getByText("Keyword")).toBeInTheDocument();
    expect(screen.getByText("Position")).toBeInTheDocument();
    expect(screen.getByText("Vol.")).toBeInTheDocument();
    expect(screen.getByText("Diff.")).toBeInTheDocument();
    expect(screen.getByText("Intent")).toBeInTheDocument();
  });

  it("renders keyword count footer", () => {
    render(<KeywordTable keywords={mockKeywords} onSearch={jest.fn()} />);
    expect(screen.getByText("4 keywords")).toBeInTheDocument();
  });

  it("handles empty keywords array without crashing", () => {
    render(<KeywordTable keywords={[]} onSearch={jest.fn()} />);
    expect(screen.getByText("0 keywords")).toBeInTheDocument();
  });

  it("calls onSearch callback when typing", () => {
    const onSearch = jest.fn();
    render(<KeywordTable keywords={mockKeywords} onSearch={onSearch} />);
    const searchInput = screen.getByPlaceholderText(/search keywords/i);
    fireEvent.change(searchInput, { target: { value: "rank" } });
    expect(onSearch).toHaveBeenCalledWith("rank");
  });
});
