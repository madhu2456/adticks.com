import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { LocationList } from "@/components/geo/LocationList";
import { LocalRankCards } from "@/components/geo/LocalRankCards";
import { ReviewDashboard } from "@/components/geo/ReviewDashboard";
import { CitationAudit } from "@/components/geo/CitationAudit";
import { Location, LocalRank, ReviewSummary, Citation, NAPCheckResult } from "@/lib/types";

// Mock data
const mockLocation: Location = {
  id: "1",
  project_id: "proj-1",
  name: "New York Branch",
  address: "123 Main Street",
  city: "New York",
  state: "NY",
  country: "USA",
  postal_code: "10001",
  phone: "+1-212-555-0123",
  latitude: 40.7128,
  longitude: -74.006,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

const mockLocations: Location[] = [
  mockLocation,
  {
    ...mockLocation,
    id: "2",
    name: "Los Angeles Branch",
    city: "Los Angeles",
    state: "CA",
  },
  {
    ...mockLocation,
    id: "3",
    name: "Chicago Branch",
    city: "Chicago",
    state: "IL",
  },
];

const mockRanks: LocalRank[] = [
  {
    id: "rank-1",
    location_id: "1",
    keyword: "pizza near me",
    google_maps_rank: 2,
    local_pack_position: 1,
    local_search_rank: 3,
    device: "desktop",
    timestamp: new Date().toISOString(),
    created_at: new Date().toISOString(),
  },
  {
    id: "rank-2",
    location_id: "1",
    keyword: "best pizza in NYC",
    google_maps_rank: 5,
    local_search_rank: 8,
    device: "mobile",
    timestamp: new Date().toISOString(),
    created_at: new Date().toISOString(),
  },
];

const mockReviewSummary: ReviewSummary = {
  id: "summary-1",
  location_id: "1",
  total_reviews: 150,
  average_rating: 4.5,
  five_star: 100,
  four_star: 35,
  three_star: 10,
  two_star: 3,
  one_star: 2,
  positive_count: 145,
  negative_count: 3,
  neutral_count: 2,
  google_reviews: 80,
  yelp_reviews: 50,
  facebook_reviews: 20,
  last_updated: new Date().toISOString(),
  created_at: new Date().toISOString(),
};

const mockCitations: Citation[] = [
  {
    id: "cit-1",
    location_id: "1",
    source_name: "Google Business",
    url: "https://business.google.com/123",
    consistency_score: 1.0,
    name_match: true,
    address_match: true,
    phone_match: true,
    business_name: "New York Branch",
    citation_address: "123 Main Street",
    citation_phone: "+1-212-555-0123",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "cit-2",
    location_id: "1",
    source_name: "Yelp",
    url: "https://yelp.com/biz/123",
    consistency_score: 0.67,
    name_match: true,
    address_match: true,
    phone_match: false,
    business_name: "New York Branch",
    citation_address: "123 Main Street",
    citation_phone: "212-555-9999",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

const mockNAPCheck: NAPCheckResult = {
  location_id: "1",
  total_citations: 2,
  consistent_citations: 1,
  consistency_percentage: 50,
  issues: [
    {
      citation_id: "cit-2",
      source: "Yelp",
      url: "https://yelp.com/biz/123",
      issues: ["Phone mismatch: Expected '+1-212-555-0123', found '212-555-9999'"],
    },
  ],
};

// ============================================================================
// LocationList Tests
// ============================================================================

describe("LocationList Component", () => {
  it("renders empty state", () => {
    render(<LocationList locations={[]} />);
    expect(screen.getByText("No locations yet")).toBeInTheDocument();
  });

  it("renders location list", () => {
    render(<LocationList locations={mockLocations} />);
    expect(screen.getByText("New York Branch")).toBeInTheDocument();
    expect(screen.getByText("Los Angeles Branch")).toBeInTheDocument();
    expect(screen.getByText("Chicago Branch")).toBeInTheDocument();
  });

  it("filters locations by search", () => {
    render(<LocationList locations={mockLocations} />);
    const input = screen.getByPlaceholderText("Search locations...");
    fireEvent.change(input, { target: { value: "Los Angeles" } });
    expect(screen.getByText("Los Angeles Branch")).toBeInTheDocument();
    expect(screen.queryByText("New York Branch")).not.toBeInTheDocument();
  });

  it("calls onAdd callback", () => {
    const onAdd = jest.fn();
    render(<LocationList locations={mockLocations} onAdd={onAdd} />);
    const addButton = screen.getByText(/Add Location/i);
    fireEvent.click(addButton);
    expect(onAdd).toHaveBeenCalled();
  });

  it("expands location details", () => {
    render(<LocationList locations={mockLocations} />);
    const location = screen.getByText("New York Branch").closest("div");
    fireEvent.click(location!);
    expect(screen.getByText("Edit")).toBeInTheDocument();
    expect(screen.getByText("Delete")).toBeInTheDocument();
  });

  it("calls onEdit callback", () => {
    const onEdit = jest.fn();
    render(<LocationList locations={mockLocations} onEdit={onEdit} />);
    const location = screen.getByText("New York Branch").closest("div");
    fireEvent.click(location!);
    const editButton = screen.getByText("Edit");
    fireEvent.click(editButton);
    expect(onEdit).toHaveBeenCalledWith(mockLocations[0]);
  });

  it("calls onDelete callback", () => {
    const onDelete = jest.fn();
    render(<LocationList locations={mockLocations} onDelete={onDelete} />);
    const location = screen.getByText("New York Branch").closest("div");
    fireEvent.click(location!);
    const deleteButton = screen.getByText("Delete");
    fireEvent.click(deleteButton);
    expect(onDelete).toHaveBeenCalledWith(mockLocations[0]);
  });

  it("displays phone number", () => {
    render(<LocationList locations={[mockLocation]} />);
    expect(screen.getByText("+1-212-555-0123")).toBeInTheDocument();
  });
});

// ============================================================================
// LocalRankCards Tests
// ============================================================================

describe("LocalRankCards Component", () => {
  it("renders empty state", () => {
    render(<LocalRankCards ranks={[]} />);
    expect(screen.getByText("No local rankings yet")).toBeInTheDocument();
  });

  it("renders local ranks", () => {
    render(<LocalRankCards ranks={mockRanks} />);
    expect(screen.getByText("pizza near me")).toBeInTheDocument();
    expect(screen.getByText("best pizza in NYC")).toBeInTheDocument();
  });

  it("displays device type", () => {
    render(<LocalRankCards ranks={mockRanks} />);
    const deviceTexts = screen.getAllByText(/desktop|mobile/);
    expect(deviceTexts.length).toBeGreaterThan(0);
  });

  it("respects maxRows prop", () => {
    render(<LocalRankCards ranks={mockRanks} maxRows={1} />);
    expect(screen.getByText("pizza near me")).toBeInTheDocument();
    expect(screen.queryByText("best pizza in NYC")).not.toBeInTheDocument();
    expect(screen.getByText("+1 more rankings")).toBeInTheDocument();
  });
});

// ============================================================================
// ReviewDashboard Tests
// ============================================================================

describe("ReviewDashboard Component", () => {
  it("renders empty state", () => {
    render(<ReviewDashboard />);
    expect(screen.getByText("No review data available")).toBeInTheDocument();
  });

  it("renders review summary", () => {
    render(<ReviewDashboard summary={mockReviewSummary} />);
    expect(screen.getByText("4.5")).toBeInTheDocument();
    expect(screen.getByText("150")).toBeInTheDocument();
  });

  it("displays star distribution", () => {
    render(<ReviewDashboard summary={mockReviewSummary} />);
    expect(screen.getByText("100")).toBeInTheDocument();
    expect(screen.getByText("35")).toBeInTheDocument();
  });

  it("displays sentiment breakdown", () => {
    render(<ReviewDashboard summary={mockReviewSummary} />);
    expect(screen.getByText("Positive")).toBeInTheDocument();
    expect(screen.getByText("Neutral")).toBeInTheDocument();
    expect(screen.getByText("Negative")).toBeInTheDocument();
    expect(screen.getByText("145")).toBeInTheDocument();
  });

  it("displays reviews by source", () => {
    render(<ReviewDashboard summary={mockReviewSummary} />);
    expect(screen.getByText("Google")).toBeInTheDocument();
    expect(screen.getByText("Yelp")).toBeInTheDocument();
    expect(screen.getByText("Facebook")).toBeInTheDocument();
  });
});

// ============================================================================
// CitationAudit Tests
// ============================================================================

describe("CitationAudit Component", () => {
  it("renders empty state", () => {
    render(<CitationAudit citations={[]} />);
    expect(screen.getByText("No citations found")).toBeInTheDocument();
  });

  it("renders citations", () => {
    render(<CitationAudit citations={mockCitations} />);
    expect(screen.getByText("Google Business")).toBeInTheDocument();
    expect(screen.getByText("Yelp")).toBeInTheDocument();
  });

  it("displays NAP check summary", () => {
    render(<CitationAudit citations={mockCitations} napCheck={mockNAPCheck} />);
    expect(screen.getByText("NAP Consistency Check")).toBeInTheDocument();
    expect(screen.getByText("50%")).toBeInTheDocument();
  });

  it("shows NAP match indicators", () => {
    render(<CitationAudit citations={mockCitations} />);
    const matchTexts = screen.getAllByText(/Match|Mismatch/);
    expect(matchTexts.length).toBeGreaterThan(0);
  });

  it("displays citation details", () => {
    render(<CitationAudit citations={mockCitations} />);
    const addresses = screen.getAllByText("123 Main Street");
    const phones = screen.getAllByText("+1-212-555-0123");
    expect(addresses.length).toBeGreaterThan(0);
    expect(phones.length).toBeGreaterThan(0);
  });

  it("respects maxRows prop", () => {
    render(<CitationAudit citations={mockCitations} maxRows={1} />);
    expect(screen.getByText("Google Business")).toBeInTheDocument();
    expect(screen.queryByText("Yelp")).not.toBeInTheDocument();
    expect(screen.getByText("+1 more citations")).toBeInTheDocument();
  });
});
