"use client";
import React, { useState } from "react";
import { Search, ArrowUp, ArrowDown, Minus, ChevronUp, ChevronDown } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Keyword, KeywordIntent } from "@/lib/types";
import { formatNumber, getDifficultyColor, cn } from "@/lib/utils";

interface KeywordTableProps {
  keywords?: Keyword[];
  loading?: boolean;
  onSearch?: (query: string) => void;
}

type SortKey = "keyword" | "difficulty" | "volume" | "position";

const intentVariantMap: Record<KeywordIntent, "informational" | "transactional" | "commercial" | "navigational"> = {
  informational: "informational",
  transactional: "transactional",
  commercial: "commercial",
  navigational: "navigational",
};

export function KeywordTable({ keywords = [], loading, onSearch }: KeywordTableProps) {
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("volume");
  const [sortAsc, setSortAsc] = useState(false);

  const handleSearch = (v: string) => {
    setSearch(v);
    onSearch?.(v);
  };

  const handleSort = (key: SortKey) => {
    if (sortKey === key) setSortAsc(!sortAsc);
    else { setSortKey(key); setSortAsc(false); }
  };

  const filtered = keywords
    .filter((k) => k.keyword.toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => {
      const va = sortKey === "keyword" ? a.keyword : (a[sortKey] ?? 999);
      const vb = sortKey === "keyword" ? b.keyword : (b[sortKey] ?? 999);
      if (typeof va === "string" && typeof vb === "string") {
        return sortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
      }
      return sortAsc ? (va as number) - (vb as number) : (vb as number) - (va as number);
    });

  const SortIcon = ({ col }: { col: SortKey }) => {
    if (sortKey !== col) return <ChevronUp className="h-3 w-3 opacity-30" />;
    return sortAsc ? <ChevronUp className="h-3 w-3 text-primary" /> : <ChevronDown className="h-3 w-3 text-primary" />;
  };

  if (loading) {
    return (
      <div>
        <Skeleton className="h-9 w-64 mb-4" />
        <div className="space-y-2">
          {[1, 2, 3, 4, 5].map((i) => <Skeleton key={i} className="h-12 w-full" />)}
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-4 relative">
        <Search className="absolute left-3 top-2.5 h-4 w-4 text-text-muted" />
        <Input
          placeholder="Search keywords..."
          value={search}
          onChange={(e) => handleSearch(e.target.value)}
          className="pl-9 w-72"
        />
      </div>
      <div className="rounded-xl border border-border overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-surface2/50">
              {[
                { key: "keyword" as SortKey, label: "Keyword" },
                { key: null, label: "Intent" },
                { key: "difficulty" as SortKey, label: "Difficulty" },
                { key: "volume" as SortKey, label: "Volume" },
                { key: "position" as SortKey, label: "Position" },
                { key: null, label: "Change" },
              ].map(({ key, label }) => (
                <th
                  key={label}
                  className={cn("px-4 py-3 text-left text-xs font-semibold text-text-muted uppercase tracking-wide", key && "cursor-pointer hover:text-text-primary")}
                  onClick={() => key && handleSort(key)}
                >
                  <div className="flex items-center gap-1">
                    {label}
                    {key && <SortIcon col={key} />}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((kw, i) => (
              <tr
                key={kw.id}
                className={cn("border-b border-border last:border-0 hover:bg-surface2/30 transition-colors", i % 2 === 0 ? "" : "bg-surface2/10")}
              >
                <td className="px-4 py-3 font-medium text-text-primary max-w-xs">
                  <span className="truncate block">{kw.keyword}</span>
                </td>
                <td className="px-4 py-3">
                  <Badge variant={intentVariantMap[kw.intent]} className="capitalize">
                    {kw.intent}
                  </Badge>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="w-16 h-1.5 bg-surface2 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{ width: `${kw.difficulty}%`, backgroundColor: getDifficultyColor(kw.difficulty) }}
                      />
                    </div>
                    <span className="text-xs text-text-muted">{kw.difficulty}</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-text-muted">{formatNumber(kw.volume, true)}</td>
                <td className="px-4 py-3 font-semibold text-text-primary">
                  {kw.position ?? "—"}
                </td>
                <td className="px-4 py-3">
                  {kw.position_change === 0 ? (
                    <span className="flex items-center gap-1 text-text-muted text-xs"><Minus className="h-3 w-3" />0</span>
                  ) : kw.position_change > 0 ? (
                    <span className="flex items-center gap-1 text-success text-xs"><ArrowUp className="h-3 w-3" />{kw.position_change}</span>
                  ) : (
                    <span className="flex items-center gap-1 text-danger text-xs"><ArrowDown className="h-3 w-3" />{Math.abs(kw.position_change)}</span>
                  )}
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-text-muted text-sm">
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
