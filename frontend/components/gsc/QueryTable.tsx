"use client";
import React, { useState, useMemo } from "react";
import { Search, ChevronUp, ChevronDown, ArrowUpRight, ArrowDownRight, Minus, ChevronLeft, ChevronRight } from "lucide-react";

interface QueryRow {
  query: string;
  clicks: number;
  impressions: number;
  ctr: number;
  position: number;
  positionChange?: number;
}

interface QueryTableProps {
  data: QueryRow[];
  title?: string;
}

type SortKey = keyof QueryRow;
type SortDir = "asc" | "desc";

function CTRBadge({ ctr }: { ctr: number }) {
  const color =
    ctr >= 5 ? "text-[#10b981] bg-[#10b981]/10" :
    ctr >= 2 ? "text-[#f59e0b] bg-[#f59e0b]/10" :
    "text-[#ef4444] bg-[#ef4444]/10";
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${color}`}>
      {ctr.toFixed(1)}%
    </span>
  );
}

function PositionCell({ position, change }: { position: number; change?: number }) {
  const Icon = !change ? Minus : change > 0 ? ArrowUpRight : ArrowDownRight;
  const color = !change ? "text-[#475569]" : change > 0 ? "text-[#10b981]" : "text-[#ef4444]";
  return (
    <div className="flex items-center gap-1.5">
      <span className="text-[#f1f5f9] text-sm">{position.toFixed(1)}</span>
      {change !== undefined && (
        <span className={`flex items-center text-xs font-medium ${color}`}>
          <Icon className="h-3 w-3" />
          {Math.abs(change)}
        </span>
      )}
    </div>
  );
}

const PAGE_SIZE = 10;

export function QueryTable({ data, title = "Top Queries" }: QueryTableProps) {
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("clicks");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [page, setPage] = useState(1);

  function handleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
    setPage(1);
  }

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    return data.filter((row) => row.query.toLowerCase().includes(q));
  }, [data, search]);

  const sorted = useMemo(() => {
    return [...filtered].sort((a, b) => {
      const av = a[sortKey] as number;
      const bv = b[sortKey] as number;
      return sortDir === "asc" ? av - bv : bv - av;
    });
  }, [filtered, sortKey, sortDir]);

  const totalPages = Math.ceil(sorted.length / PAGE_SIZE);
  const paginated = sorted.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  function SortIcon({ col }: { col: SortKey }) {
    if (col !== sortKey) return <ChevronUp className="h-3 w-3 text-[#475569] ml-1" />;
    return sortDir === "asc"
      ? <ChevronUp className="h-3 w-3 text-[#6366f1] ml-1" />
      : <ChevronDown className="h-3 w-3 text-[#6366f1] ml-1" />;
  }

  const cols: { key: SortKey; label: string; align?: string }[] = [
    { key: "query", label: "Query" },
    { key: "clicks", label: "Clicks", align: "text-right" },
    { key: "impressions", label: "Impressions", align: "text-right" },
    { key: "ctr", label: "CTR", align: "text-center" },
    { key: "position", label: "Avg Position", align: "text-center" },
  ];

  return (
    <div className="bg-[#1e293b] rounded-xl border border-[#334155] overflow-hidden">
      <div className="flex items-center justify-between px-5 py-4 border-b border-[#334155]">
        <h3 className="text-[#f1f5f9] font-semibold text-sm">{title}</h3>
        <div className="relative w-64">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[#475569]" />
          <input
            type="text"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            placeholder="Filter queries..."
            className="w-full bg-[#0f172a] border border-[#334155] rounded-lg pl-8 pr-3 py-1.5 text-sm text-[#f1f5f9] placeholder-[#475569] focus:outline-none focus:ring-2 focus:ring-[#6366f1]/40 focus:border-[#6366f1] transition-colors"
          />
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-[#0f172a]/40">
              {cols.map((col) => (
                <th
                  key={col.key}
                  onClick={() => col.key !== "query" && handleSort(col.key)}
                  className={`px-5 py-3 text-xs font-medium text-[#94a3b8] uppercase tracking-wide cursor-pointer hover:text-[#f1f5f9] select-none ${col.align || "text-left"}`}
                >
                  <span className="inline-flex items-center">
                    {col.label}
                    {col.key !== "query" && <SortIcon col={col.key} />}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paginated.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-5 py-12 text-center text-[#94a3b8] text-sm">
                  No queries match your filter.
                </td>
              </tr>
            ) : (
              paginated.map((row, idx) => (
                <tr key={idx} className="border-t border-[#334155]/50 hover:bg-[#334155]/20 transition-colors">
                  <td className="px-5 py-3.5 text-[#f1f5f9] max-w-xs truncate font-medium">{row.query}</td>
                  <td className="px-5 py-3.5 text-[#f1f5f9] text-right">{row.clicks.toLocaleString()}</td>
                  <td className="px-5 py-3.5 text-[#94a3b8] text-right">{row.impressions.toLocaleString()}</td>
                  <td className="px-5 py-3.5 text-center">
                    <CTRBadge ctr={row.ctr} />
                  </td>
                  <td className="px-5 py-3.5 text-center">
                    <PositionCell position={row.position} change={row.positionChange} />
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between px-5 py-3 border-t border-[#334155] bg-[#0f172a]/20">
          <span className="text-xs text-[#94a3b8]">
            Showing {(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, sorted.length)} of {sorted.length}
          </span>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="p-1.5 rounded text-[#94a3b8] hover:text-[#f1f5f9] hover:bg-[#334155] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            {Array.from({ length: totalPages }, (_, i) => i + 1)
              .filter((p) => Math.abs(p - page) <= 2)
              .map((p) => (
                <button
                  key={p}
                  onClick={() => setPage(p)}
                  className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                    p === page
                      ? "bg-[#6366f1] text-white"
                      : "text-[#94a3b8] hover:text-[#f1f5f9] hover:bg-[#334155]"
                  }`}
                >
                  {p}
                </button>
              ))}
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="p-1.5 rounded text-[#94a3b8] hover:text-[#f1f5f9] hover:bg-[#334155] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
