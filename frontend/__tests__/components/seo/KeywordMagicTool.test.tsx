import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { KeywordMagicTool } from "@/components/seo/KeywordMagicTool";

jest.mock("@/hooks/useSEO", () => ({
  useKeywordIdeas: jest.fn(),
  useKeywordMagic: jest.fn(),
}));

import { useKeywordIdeas, useKeywordMagic } from "@/hooks/useSEO";

const mIdeas = useKeywordIdeas as jest.Mock;
const mMagic = useKeywordMagic as jest.Mock;

beforeEach(() => {
  mIdeas.mockReturnValue({ isLoading: false, data: [] });
  mMagic.mockReturnValue({ isPending: false, mutateAsync: jest.fn() });
});

describe("KeywordMagicTool", () => {
  it("renders the seed input and Generate button", () => {
    render(<KeywordMagicTool projectId="p1"/>);
    expect(screen.getByPlaceholderText(/seed keyword/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /generate ideas/i })).toBeInTheDocument();
  });

  it("disables Generate when seed is empty", () => {
    render(<KeywordMagicTool projectId="p1"/>);
    expect(screen.getByRole("button", { name: /generate ideas/i })).toBeDisabled();
  });

  it("enables Generate when a seed is typed", () => {
    render(<KeywordMagicTool projectId="p1"/>);
    fireEvent.change(screen.getByPlaceholderText(/seed keyword/i), { target: { value: "seo" } });
    expect(screen.getByRole("button", { name: /generate ideas/i })).not.toBeDisabled();
  });

  it("calls mutateAsync when Generate clicked", async () => {
    const mutateAsync = jest.fn().mockResolvedValue([]);
    mMagic.mockReturnValue({ isPending: false, mutateAsync });
    render(<KeywordMagicTool projectId="p1"/>);
    fireEvent.change(screen.getByPlaceholderText(/seed keyword/i), { target: { value: "seo" } });
    fireEvent.click(screen.getByRole("button", { name: /generate ideas/i }));
    await waitFor(() => expect(mutateAsync).toHaveBeenCalledWith({
      projectId: "p1",
      payload: { seed: "seo", location: "us", include_questions: true, limit: 80 },
    }));
  });

  it("renders rows from useKeywordIdeas", () => {
    mIdeas.mockReturnValue({
      isLoading: false,
      data: [
        { id: "k1", keyword: "what is seo", match_type: "question",
          intent: "informational", volume: 2000, difficulty: 30, cpc: 0.5,
          serp_features: [] },
        { id: "k2", keyword: "best seo tools", match_type: "phrase",
          intent: "commercial", volume: 4000, difficulty: 60, cpc: 4.2,
          serp_features: [] },
      ],
    });
    render(<KeywordMagicTool projectId="p1"/>);
    expect(screen.getByText("what is seo")).toBeInTheDocument();
    expect(screen.getByText("best seo tools")).toBeInTheDocument();
    expect(screen.getByText("$0.50")).toBeInTheDocument();
    expect(screen.getByText("$4.20")).toBeInTheDocument();
  });

  it("computes summary stats from ideas", () => {
    mIdeas.mockReturnValue({
      isLoading: false,
      data: [
        { id: "k1", keyword: "a", match_type: "question", intent: "informational",
          volume: 1000, difficulty: 20, cpc: 0.5, serp_features: [] },
        { id: "k2", keyword: "b", match_type: "phrase", intent: "commercial",
          volume: 3000, difficulty: 40, cpc: 1, serp_features: [] },
      ],
    });
    render(<KeywordMagicTool projectId="p1"/>);
    expect(screen.getByText("Ideas")).toBeInTheDocument();
    expect(screen.getByText("Total Volume")).toBeInTheDocument();
    expect(screen.getByText("4,000")).toBeInTheDocument(); // total volume
    expect(screen.getByText("30")).toBeInTheDocument(); // avg difficulty
  });
});
