import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { ReportBuilder } from "@/components/seo/ReportBuilder";

jest.mock("@/hooks/useSEO", () => ({
  useReports: jest.fn(),
  useGenerateReport: jest.fn(),
}));

import { useReports, useGenerateReport } from "@/hooks/useSEO";

const mReports = useReports as jest.Mock;
const mGenerate = useGenerateReport as jest.Mock;

beforeEach(() => {
  mReports.mockReturnValue({ isLoading: false, data: [] });
  mGenerate.mockReturnValue({ isPending: false, mutate: jest.fn() });
});

describe("ReportBuilder", () => {
  it("renders form with default values", () => {
    render(<ReportBuilder projectId="p1"/>);
    expect(screen.getByDisplayValue("Monthly SEO Report")).toBeInTheDocument();
    expect(screen.getByDisplayValue("AdTicks")).toBeInTheDocument();
  });

  it("calls generate with full payload", () => {
    const mutate = jest.fn();
    mGenerate.mockReturnValue({ isPending: false, mutate });
    render(<ReportBuilder projectId="p1"/>);
    fireEvent.click(screen.getByRole("button", { name: /generate report/i }));
    expect(mutate).toHaveBeenCalledWith({
      projectId: "p1",
      payload: expect.objectContaining({
        report_type: "full_seo",
        title: "Monthly SEO Report",
        branding: expect.objectContaining({ brand_name: "AdTicks" }),
      }),
    });
  });

  it("renders empty state when no reports exist", () => {
    render(<ReportBuilder projectId="p1"/>);
    expect(screen.getByText(/no reports generated yet/i)).toBeInTheDocument();
  });

  it("renders generated report rows with download link", () => {
    mReports.mockReturnValue({
      isLoading: false,
      data: [{
        id: "r1", title: "March Report", report_type: "full_seo",
        timestamp: new Date().toISOString(), file_url: "/api/storage/r.pdf",
      }],
    });
    render(<ReportBuilder projectId="p1"/>);
    expect(screen.getByText("March Report")).toBeInTheDocument();
    expect(screen.getByText("full_seo")).toBeInTheDocument();
    const link = screen.getByRole("link", { name: /download/i });
    expect(link).toHaveAttribute("href", "/api/storage/r.pdf");
  });

  it("changing report type updates the select", () => {
    render(<ReportBuilder projectId="p1"/>);
    const select = screen.getByDisplayValue("Full SEO Report") as HTMLSelectElement;
    fireEvent.change(select, { target: { value: "backlinks" } });
    expect(select.value).toBe("backlinks");
  });
});
