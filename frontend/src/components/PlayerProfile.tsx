import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import type { PlayerSeasonDetail } from "../types/Playertype";
import { deltaColor, formatDelta, formatSalary, formatStat, verdictColor } from "../utils/format";

interface StatTileProps {
  label: string;
  value: string;
}

function StatTile({ label, value }: StatTileProps) {
  return (
    <div className="flex-1 rounded-xl border border-white/[0.08] bg-[#131418] px-4 py-3 text-center">
      <div className="font-mono text-2xl font-semibold tabular-nums text-white">{value}</div>
      <div className="mt-1 text-xs font-medium text-white/40">{label}</div>
    </div>
  );
}

export function PlayerProfile() {
  const { playerId } = useParams();
  const [seasons, setSeasons] = useState<PlayerSeasonDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetch(`http://localhost:8000/players/${playerId}`)
      .then((res) => {
        if (!res.ok) throw new Error(res.status === 404 ? "Player not found." : `Request failed: ${res.status}`);
        return res.json();
      })
      .then(setSeasons)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [playerId]);

  const latest = seasons[0];

  return (
    <div className="px-10 py-6">
      <Link to="/" className="mb-6 inline-block text-sm text-white/40 hover:text-white">
        ← Back to players
      </Link>

      {loading && <p className="text-sm text-white/40">Loading player…</p>}
      {error && <p className="text-sm text-[#FF5000]">{error}</p>}

      {!loading && !error && latest && (
        <>
          <div className="mb-6 flex items-center gap-5">
            {latest.headshot_url && (
              <img
                src={latest.headshot_url}
                alt={latest.full_name}
                className="h-32 w-32 rounded-2xl border border-white/[0.08] bg-[#131418] object-contain"
              />
            )}
            <div>
              <h1 className="text-3xl font-semibold text-white">{latest.full_name}</h1>
              <p className="mt-1 text-sm text-white/40">
                {latest.position ?? "—"} · {latest.team} · {latest.season} season
              </p>
            </div>
          </div>

          <div className="mb-3 flex gap-3">
            <StatTile label="PTS" value={formatStat(latest.points)} />
            <StatTile label="REB" value={formatStat(latest.rebounds)} />
            <StatTile label="AST" value={formatStat(latest.assists)} />
            <StatTile label="GP" value={latest.games_played?.toString() ?? "—"} />
          </div>

          <div className="mb-6 flex flex-col gap-5 rounded-xl border border-white/[0.08] bg-[#131418] px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex flex-wrap items-center gap-x-12 gap-y-4">
              <div>
                <div className="text-sm font-medium text-white/40">Current salary</div>
                <div className="font-mono text-3xl font-semibold tabular-nums text-white">
                  {formatSalary(latest.salary)}
                </div>
              </div>
              <div>
                <div className="text-sm font-medium text-white/40">Predicted salary</div>
                <div className="font-mono text-3xl font-semibold tabular-nums text-white/55">
                  {formatSalary(latest.predicted_salary)}
                </div>
              </div>
              {latest.delta_pct != null && (
                <div>
                  <div className="text-sm font-medium text-white/40">Δ</div>
                  <div className={`font-mono text-3xl font-semibold tabular-nums ${deltaColor(latest.delta_pct)}`}>
                    {formatDelta(latest.delta_pct)}
                  </div>
                </div>
              )}
            </div>
            {latest.verdict && (
              <span
                className="inline-flex w-fit items-center gap-1.5 rounded-full bg-white/[0.06] px-4 py-2 text-sm font-medium"
                style={{ color: verdictColor(latest.verdict) }}
              >
                <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: verdictColor(latest.verdict) }} />
                {latest.verdict}
              </span>
            )}
          </div>

          <h2 className="mb-3 text-base font-semibold text-white">
            Season History{" "}
            <span className="text-sm font-normal text-white/40">
              · last {seasons.length} season{seasons.length === 1 ? "" : "s"}
            </span>
          </h2>

          <div className="overflow-hidden rounded-2xl border border-white/[0.08] bg-[#131418] shadow-xl shadow-black/40">
            <table className="w-full border-collapse text-left text-sm">
              <thead>
                <tr className="border-b border-white/[0.08] text-[11px] uppercase tracking-wider text-white/40">
                  <th className="px-5 py-3.5 font-medium">Season</th>
                  <th className="px-5 py-3.5 font-medium">Team</th>
                  <th className="px-5 py-3.5 text-right font-medium">GP</th>
                  <th className="px-5 py-3.5 text-right font-medium">PTS</th>
                  <th className="px-5 py-3.5 text-right font-medium">REB</th>
                  <th className="px-5 py-3.5 text-right font-medium">AST</th>
                  <th className="px-5 py-3.5 text-right font-medium">Salary</th>
                  <th className="px-5 py-3.5 text-right font-medium">Predicted</th>
                  <th className="px-5 py-3.5 text-right font-medium">Delta</th>
                  <th className="px-5 py-3.5 font-medium">Verdict</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.06]">
                {seasons.map((s) => (
                  <tr key={`${s.player_id}-${s.season}-${s.team}`} className="odd:bg-white/[0.015]">
                    <td className="px-5 py-3.5 font-semibold text-white">{s.season}</td>
                    <td className="px-5 py-3.5 text-white/45">{s.team}</td>
                    <td className="px-5 py-3.5 text-right tabular-nums text-white/80">
                      {s.games_played ?? "—"}
                    </td>
                    <td className="px-5 py-3.5 text-right tabular-nums text-white/80">
                      {formatStat(s.points)}
                    </td>
                    <td className="px-5 py-3.5 text-right tabular-nums text-white/80">
                      {formatStat(s.rebounds)}
                    </td>
                    <td className="px-5 py-3.5 text-right tabular-nums text-white/80">
                      {formatStat(s.assists)}
                    </td>
                    <td className="px-5 py-3.5 text-right tabular-nums text-white">
                      {formatSalary(s.salary)}
                    </td>
                    <td className="px-5 py-3.5 text-right tabular-nums text-white/55">
                      {formatSalary(s.predicted_salary)}
                    </td>
                    <td className={`px-5 py-3.5 text-right tabular-nums font-semibold ${deltaColor(s.delta_pct)}`}>
                      {formatDelta(s.delta_pct)}
                    </td>
                    <td className="px-5 py-3.5">
                      <span
                        className="inline-flex items-center gap-1.5 text-xs font-medium"
                        style={{ color: verdictColor(s.verdict) }}
                      >
                        <span
                          className="h-1.5 w-1.5 rounded-full"
                          style={{ backgroundColor: verdictColor(s.verdict) }}
                        />
                        {s.verdict ?? "—"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
