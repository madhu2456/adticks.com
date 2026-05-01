import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { LogFileAnalyzer } from "@/components/seo/LogFileAnalyzer";

jest.mock("@/hooks/useSEO", () => ({
  useLogEvents: jest.fn(),
  useUploadLogFile: jest.fn(),
}));

import { useLogEvents, useUploadLogFile } from "@/hooks/useSEO";

const mEvents = useLogEvents as jest.Mock;
const mUpload = useUploadLogFile as jest.Mock;

beforeEach(() => {
  mEvents.mockReturnValue({ isLoading: false, data: [] });
  mUpload.mockReturnValue({ isPending: false, mutateAsync: jest.fn() });
});

describe("LogFileAnalyzer", () => {
  it("renders the upload button and empty state", () => {
    render(<LogFileAnalyzer projectId="p1"/>);
    expect(screen.getByRole("button", { name: /upload log file/i })).toBeInTheDocument();
    expect(screen.getByText(/upload a log file/i)).toBeInTheDocument();
  });

  it("supports the documented bots in the description", () => {
    render(<LogFileAnalyzer projectId="p1"/>);
    expect(screen.getByText(/Googlebot/)).toBeInTheDocument();
    expect(screen.getByText(/ClaudeBot/)).toBeInTheDocument();
  });

  it("renders log event rows when data present", () => {
    mEvents.mockReturnValue({
      isLoading: false,
      data: [{
        id: "e1", bot: "googlebot", url: "/page1", status_code: 200,
        hits: 5, last_crawled: new Date().toISOString(),
      }],
    });
    render(<LogFileAnalyzer projectId="p1"/>);
    expect(screen.getByText("/page1")).toBeInTheDocument();
    expect(screen.getByText("googlebot")).toBeInTheDocument();
    expect(screen.getByText("200")).toBeInTheDocument();
  });

  it("calls upload mutation with selected file", async () => {
    const mutateAsync = jest.fn().mockResolvedValue({ summary: { total_hits: 0, unique_urls: 0, crawl_waste_pct: 0, bots: {} } });
    mUpload.mockReturnValue({ isPending: false, mutateAsync });
    const { container } = render(<LogFileAnalyzer projectId="p1"/>);
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(["log line"], "access.log", { type: "text/plain" });
    
    await React.act(async () => {
      fireEvent.change(input, { target: { files: [file] } });
      await new Promise((r) => setTimeout(r, 0));
    });
    
    expect(mutateAsync).toHaveBeenCalled();
    expect(mutateAsync.mock.calls[0][0].projectId).toBe("p1");
  });
});
