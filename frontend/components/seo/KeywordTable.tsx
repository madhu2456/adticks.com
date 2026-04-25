"use client";
import React, { useState } from "react";
import { Search, ArrowUp, ArrowDown, Minus, ChevronUp, ChevronDown, AlertTriangle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { 
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface KeywordTableProps {
  keywords: any[];
  onSearch: (v: string) => void;
}

export function KeywordTable({ keywords, onSearch }: KeywordTableProps) {
  const [search, setSearch] = useState("");

  const handleSearchChange = (val: string) => {
    setSearch(val);
    onSearch(val);
  };

  const filtered = keywords.filter((k) =>
    k.keyword.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-4">
      <div className="relative">
        <Search className="absolute left-3 top-2.5 h-4 w-4 text-text-muted" />
        <Input
          placeholder="Search keywords..."
          className="pl-9"
          value={search}
          onChange={(e) => handleSearchChange(e.target.value)}
        />
      </div>

      <div className="overflow-x-auto rounded-xl border border-border">
        <table className="w-full text-sm">
          <thead className="bg-surface2 border-b border-border">
            <tr className="text-left text-xs font-semibold text-text-muted uppercase tracking-wider">
              <th className="px-4 py-3">Keyword</th>
              <th className="px-4 py-3">Position</th>
              <th className="px-4 py-3">Vol.</th>
              <th className="px-4 py-3">Diff.</th>
              <th className="px-4 py-3">Intent</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((kw) => (
              <tr key={kw.id} className="border-b border-border hover:bg-surface2/50 transition-colors">
                <td className="px-4 py-4">
                   <div className="flex flex-col">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-text-primary">{kw.keyword}</span>
                      {kw.is_cannibalized && (
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger>
                              <AlertTriangle className="h-4 w-4 text-orange-500" />
                            </TooltipTrigger>
                            <TooltipContent>
                              <p className="max-w-xs text-xs">
                                <strong>Keyword Cannibalization Detected:</strong> Multiple pages on your site are competing for this keyword, which can split authority and lower rankings.
                              </p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      )}
                    </div>
                    <span className="text-[10px] text-text-muted truncate max-w-[200px]">
                      {kw.url || "No URL detected"}
                    </span>
                  </div>
                </td>
                <td className="px-4 py-4">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-text-primary">
                      {kw.position ? `#${kw.position}` : "—"}
                    </span>
                    {kw.position_change && kw.position_change !== 0 ? (
                      <span
                        className={cn(
                          "flex items-center text-[10px] font-bold",
                          kw.position_change < 0 ? "text-success" : "text-danger"
                        )}
                      >
                        {kw.position_change < 0 ? (
                          <ChevronUp size={12} />
                        ) : (
                          <ChevronDown size={12} />
                        )}
                        {Math.abs(kw.position_change)}
                      </span>
                    ) : null}
                  </div>
                </td>
                <td className="px-4 py-4 text-text-muted">
                  {kw.volume ? kw.volume.toLocaleString() : "0"}
                </td>
                <td className="px-4 py-4">
                  <span
                    className={cn(
                      "px-2 py-0.5 rounded text-[10px] font-bold",
                      kw.difficulty > 70
                        ? "bg-red-500/10 text-red-500"
                        : kw.difficulty > 30
                        ? "bg-orange-500/10 text-orange-500"
                        : "bg-green-500/10 text-green-500"
                    )}
                  >
                    {kw.difficulty || 0}
                  </span>
                </td>
                <td className="px-4 py-4">
                  <Badge variant="secondary" className="text-[10px] capitalize font-medium">
                    {kw.intent || "—"}
                  </Badge>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-10 text-center text-text-muted">
                  No keywords found matching &quot;{search}&quot;
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-text-muted mt-2">{filtered.length} keywords</p>
    </div>
  );
}
