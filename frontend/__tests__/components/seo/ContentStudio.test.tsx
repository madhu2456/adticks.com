import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { ContentStudio } from "@/components/seo/ContentStudio";

jest.mock("@/hooks/useSEO", () => ({
  useBriefs: jest.fn(),
  useCreateBrief: jest.fn(),
  useOptimizeContent: jest.fn(),
  useTopicClusters: jest.fn(),
  useBuildCluster: jest.fn(),
}));

import {
  useBriefs, useCreateBrief, useOptimizeContent, useTopicClusters, useBuildCluster,
} from "@/hooks/useSEO";

const mBriefs = useBriefs as jest.Mock;
const mCreate = useCreateBrief as jest.Mock;
const mOptimize = useOptimizeContent as jest.Mock;
const mClusters = useTopicClusters as jest.Mock;
const mBuild = useBuildCluster as jest.Mock;

beforeEach(() => {
  mBriefs.mockReturnValue({ isLoading: false, data: [] });
  mCreate.mockReturnValue({ isPending: false, mutate: jest.fn() });
  mOptimize.mockReturnValue({ isPending: false, mutate: jest.fn(), data: null });
  mClusters.mockReturnValue({ isLoading: false, data: [] });
  mBuild.mockReturnValue({ isPending: false, mutate: jest.fn() });
});

describe("ContentStudio", () => {
  it("renders briefs tab by default", () => {
    render(<ContentStudio projectId="p1"/>);
    expect(screen.getByText(/generate content brief/i)).toBeInTheDocument();
  });

  it("creates a brief when Generate clicked", () => {
    const mutate = jest.fn();
    mCreate.mockReturnValue({ isPending: false, mutate });
    render(<ContentStudio projectId="p1"/>);
    fireEvent.change(screen.getByPlaceholderText(/target keyword/i), { target: { value: "seo audit" } });
    fireEvent.click(screen.getByRole("button", { name: /generate/i }));
    expect(mutate).toHaveBeenCalledWith({
      projectId: "p1",
      payload: { target_keyword: "seo audit", target_word_count: 1500 },
    });
  });

  it("shows brief details when a brief exists", () => {
    mBriefs.mockReturnValue({
      isLoading: false,
      data: [{
        id: "b1", target_keyword: "email marketing",
        target_word_count: 1500, avg_competitor_words: 1400,
        title_suggestions: ["The Complete Guide to Email Marketing"],
        outline: ["[h2] Why It Matters"], semantic_terms: ["automation"],
        questions_to_answer: ["Why does email marketing work?"],
      }],
    });
    render(<ContentStudio projectId="p1"/>);
    expect(screen.getByText("email marketing")).toBeInTheDocument();
    expect(screen.getByText(/The Complete Guide to Email Marketing/)).toBeInTheDocument();
    expect(screen.getByText(/Why It Matters/)).toBeInTheDocument();
    expect(screen.getByText("automation")).toBeInTheDocument();
  });

  it("optimizer tab calls mutate with content", () => {
    const mutate = jest.fn();
    mOptimize.mockReturnValue({ isPending: false, mutate, data: null });
    render(<ContentStudio projectId="p1"/>);
    fireEvent.click(screen.getByRole("tab", { name: /optimizer/i }));
    fireEvent.change(screen.getByPlaceholderText(/target keyword/i), { target: { value: "kw" } });
    fireEvent.change(screen.getByPlaceholderText(/paste your draft/i), { target: { value: "<p>hi</p>" } });
    fireEvent.click(screen.getByRole("button", { name: /score/i }));
    expect(mutate).toHaveBeenCalledWith({
      projectId: "p1",
      payload: { target_keyword: "kw", content: "<p>hi</p>" },
    });
  });

  it("renders optimizer score result", () => {
    mOptimize.mockReturnValue({
      isPending: false, mutate: jest.fn(),
      data: {
        target_keyword: "kw", word_count: 800, readability_score: 70, grade_level: "easy",
        keyword_density: 1.2, headings_score: 80, semantic_coverage: 0.7, overall_score: 78,
        suggestions: [{ type: "length", text: "Add more content" }],
      },
    });
    render(<ContentStudio projectId="p1"/>);
    fireEvent.click(screen.getByRole("tab", { name: /optimizer/i }));
    expect(screen.getByText("Result")).toBeInTheDocument();
    expect(screen.getByText("78")).toBeInTheDocument();
    expect(screen.getByText("Add more content")).toBeInTheDocument();
  });

  it("clusters tab builds a cluster with the entered pillar", () => {
    const mutate = jest.fn();
    mBuild.mockReturnValue({ isPending: false, mutate });
    render(<ContentStudio projectId="p1"/>);
    fireEvent.click(screen.getByRole("tab", { name: /topic clusters/i }));
    fireEvent.change(screen.getByPlaceholderText(/pillar topic/i), { target: { value: "email marketing" } });
    fireEvent.click(screen.getByRole("button", { name: /build cluster/i }));
    expect(mutate).toHaveBeenCalledWith({ projectId: "p1", pillar: "email marketing" });
  });
});
