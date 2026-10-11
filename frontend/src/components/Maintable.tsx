import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { Player } from "../types/Playertype";
import { deltaColor, formatDelta, formatSalary, verdictColor } from "../utils/format";

type SortKey =
  | "full_name"
  | "team"
  | "points"
  | "rebounds"
  | "assists"
  | "salary"
  | "predicted_salary"
  | "delta_pct"
  | "verdict";

type SortDirection = "asc" | "desc";

const numericSortKeys = new Set<SortKey>([
  "points",
  "rebounds",
  "assists",
  "salary",
  "predicted_salary",
  "delta_pct",
]);

const columns: { key: SortKey; label: string; align: "left" | "right" }[] = [
  { key: "full_name", label: "Player", align: "left" },
  { key: "team", label: "Team", align: "left" },
  { key: "points", label: "PTS", align: "right" },
  { key: "rebounds", label: "REB", align: "right" },
  { key: "assists", label: "AST", align: "right" },
  { key: "salary", label: "Salary", align: "right" },
  { key: "predicted_salary", label: "Predicted", align: "right" },
  { key: "delta_pct", label: "Delta", align: "right" },
  { key: "verdict", label: "Verdict", align: "left" },
];

function getSortValue(player: Player, key: SortKey): number | string {
  if (numericSortKeys.has(key)) {
    const num = Number(player[key]);
    return Number.isFinite(num) ? num : -Infinity;
  }
  return (player[key] ?? "").toString().toLowerCase();
}

const PAGE_SIZE_OPTIONS = [25, 50, 100] as const;

export function MainTable() {
  const navigate = useNavigate();
  const [data, setData] = useState<Player[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [sortKey, setSortKey] = useState<SortKey | null>(null);
  const [sortDir, setSortDir] = useState<SortDirection>("asc");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState<number>(PAGE_SIZE_OPTIONS[0]);

  function toggleSort(key: SortKey) {
    setPage(1);
    if (sortKey !== key) {
      setSortKey(key);
      setSortDir(numericSortKeys.has(key) ? "desc" : "asc");
      return;
    }
    setSortDir((dir) => (dir === "asc" ? "desc" : "asc"));
  }

  function handleQueryChange(value: string) {
    setQuery(value);
    setPage(1);
  }

  function handlePageSizeChange(size: number) {
    setPageSize(size);
    setPage(1);
  }

  useEffect(() => {
    fetch("http://localhost:8000/players?limit=1000")
      .then((response) => response.json())
      .then((result: Player[]) => setData(result))
      .catch(() => setError("Couldn't load player data."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <p className="px-10 py-6 text-sm text-white/40">Loading players…</p>;
  }

  if (error) {
    return <p className="px-10 py-6 text-sm text-[#FF5000]">{error}</p>;
  }

  const normalizedQuery = query.trim().toLowerCase();
  const filteredData = normalizedQuery
    ? data.filter(
        (player) =>
          player.full_name.toLowerCase().includes(normalizedQuery) ||
          player.team.toLowerCase().includes(normalizedQuery)
      )
    : data;

  const sortedData = sortKey
    ? [...filteredData].sort((a, b) => {
        const valueA = getSortValue(a, sortKey);
        const valueB = getSortValue(b, sortKey);
        const comparison =
          typeof valueA === "number" && typeof valueB === "number"
            ? valueA - valueB
            : valueA < valueB
              ? -1
              : valueA > valueB
                ? 1
                : 0;
        return sortDir === "asc" ? comparison : -comparison;
      })
    : filteredData;

  const totalPages = Math.max(1, Math.ceil(sortedData.length / pageSize));
  const currentPage = Math.min(page, totalPages);
  const pageStart = (currentPage - 1) * pageSize;
  const pagedData = sortedData.slice(pageStart, pageStart + pageSize);

  return (
    <div className="px-10 py-6">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <input
          type="text"
          value={query}
          onChange={(event) => handleQueryChange(event.target.value)}
          placeholder="Search players or teams…"
          className="w-full max-w-sm rounded-lg border border-white/[0.08] bg-[#131418] px-3.5 py-2 text-sm text-white placeholder:text-white/40 outline-none focus:border-white/20"
        />
        <div className="flex items-center gap-2 text-xs text-white/50">
          <span>Rows per page</span>
          <select
            value={pageSize}
            onChange={(event) => handlePageSizeChange(Number(event.target.value))}
            className="rounded-lg border border-white/[0.08] bg-[#131418] px-2 py-1.5 text-xs text-white outline-none focus:border-white/20"
          >
            {PAGE_SIZE_OPTIONS.map((size) => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </select>
        </div>
      </div>
      <div className="overflow-hidden rounded-2xl border border-white/[0.08] bg-[#131418] shadow-xl shadow-black/40">
        <table className="w-full border-collapse text-left text-sm">
          <thead>
            <tr className="border-b border-white/[0.08] text-[11px] uppercase tracking-wider text-white/40">
              {columns.map((column) => (
                <th
                  key={column.key}
                  className={`px-5 py-3.5 font-medium ${column.align === "right" ? "text-right" : ""}`}
                >
                  <button
                    type="button"
                    onClick={() => toggleSort(column.key)}
                    className={`inline-flex items-center gap-1 uppercase tracking-wider hover:text-white/70 ${
                      column.align === "right" ? "flex-row-reverse" : ""
                    } ${sortKey === column.key ? "text-white/80" : ""}`}
                  >
                    {column.label}
                    <span className="text-[9px]">
                      {sortKey === column.key ? (sortDir === "asc" ? "▲" : "▼") : ""}
                    </span>
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.06]">
            {pagedData.map((player) => (
              <tr
                key={`${player.player_id}-${player.team}`}
                onClick={() => navigate(`/players/${player.player_id}`)}
                className="cursor-pointer transition-colors odd:bg-white/[0.015] hover:bg-white/[0.06]"
              >
                <td className="px-5 py-3.5 font-semibold text-white">{player.full_name}</td>
                <td className="px-5 py-3.5 text-white/45">{player.team}</td>
                <td className="px-5 py-3.5 text-right tabular-nums text-white/80">{player.points}</td>
                <td className="px-5 py-3.5 text-right tabular-nums text-white/80">{player.rebounds}</td>
                <td className="px-5 py-3.5 text-right tabular-nums text-white/80">{player.assists}</td>
                <td className="px-5 py-3.5 text-right tabular-nums text-white">
                  {formatSalary(player.salary)}
                </td>
                <td className="px-5 py-3.5 text-right tabular-nums text-white/55">
                  {formatSalary(player.predicted_salary)}
                </td>
                <td
                  className={`px-5 py-3.5 text-right tabular-nums font-semibold ${deltaColor(player.delta_pct)}`}
                >
                  {formatDelta(player.delta_pct)}
                </td>
                <td className="px-5 py-3.5">
                  <span
                    className="inline-flex items-center gap-1.5 text-xs font-medium"
                    style={{ color: verdictColor(player.verdict) }}
                  >
                    <span
                      className="h-1.5 w-1.5 rounded-full"
                      style={{ backgroundColor: verdictColor(player.verdict) }}
                    />
                    {player.verdict ?? "—"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-4 flex items-center justify-between text-xs text-white/50">
        <span>
          Showing {sortedData.length === 0 ? 0 : pageStart + 1}–
          {Math.min(pageStart + pageSize, sortedData.length)} of {sortedData.length}
        </span>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={currentPage <= 1}
            className="rounded-lg border border-white/[0.08] px-3 py-1.5 font-medium hover:bg-white/[0.06] disabled:cursor-not-allowed disabled:opacity-30"
          >
            Prev
          </button>
          <span>
            Page {currentPage} of {totalPages}
          </span>
          <button
            type="button"
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={currentPage >= totalPages}
            className="rounded-lg border border-white/[0.08] px-3 py-1.5 font-medium hover:bg-white/[0.06] disabled:cursor-not-allowed disabled:opacity-30"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}