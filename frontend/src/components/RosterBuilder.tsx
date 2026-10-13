import { useEffect, useMemo, useState } from "react";
import type { Player } from "../types/Playertype";
import type { RosterOut, RosterSummary } from "../types/Rostertype";
import { formatSalary } from "../utils/format";

const MAX_ROSTER_SIZE = 15;
const MIN_ROSTER_SIZE = 8;
const API_BASE = "http://localhost:8000";

function totalOf(players: { salary?: string | number | null }[]) {
  return players.reduce((sum, p) => {
    const num = Number(p.salary);
    return sum + (Number.isFinite(num) ? num : 0);
  }, 0);
}

function initials(name: string) {
  const parts = name.trim().split(/\s+/);
  const first = parts[0]?.[0] ?? "";
  const last = parts.length > 1 ? parts[parts.length - 1][0] : "";
  return (first + last).toUpperCase();
}

function PlayerSlot({
  name,
  position,
  team,
  salary,
  onRemove,
}: {
  name: string;
  position?: string | null;
  team?: string | null;
  salary?: string | number | null;
  onRemove: () => void;
}) {
  return (
    <div className="group relative flex h-[104px] flex-col justify-between rounded-xl border border-white/[0.08] bg-[#1a1b20] p-3 transition-colors hover:border-white/20">
      <button
        type="button"
        onClick={onRemove}
        aria-label={`Remove ${name}`}
        className="absolute right-1.5 top-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-white/[0.08] text-xs text-white/50 opacity-0 transition-opacity hover:bg-[#FF5000]/20 hover:text-[#FF5000] group-hover:opacity-100"
      >
        ×
      </button>
      {position && (
        <span className="absolute left-1.5 top-1.5 rounded bg-white/[0.08] px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wide text-white/60">
          {position}
        </span>
      )}
      <div className="flex items-center gap-2 pr-5 pt-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white/[0.06] text-xs font-bold text-white/70">
          {initials(name)}
        </div>
        <div className="min-w-0">
          <div className="truncate text-sm font-semibold text-white">{name}</div>
          <div className="truncate text-xs text-white/40">{team ?? "—"}</div>
        </div>
      </div>
      <div className="font-mono text-sm font-semibold tabular-nums text-white">{formatSalary(salary)}</div>
    </div>
  );
}

function EmptySlot() {
  return (
    <div className="flex h-[104px] items-center justify-center rounded-xl border border-dashed border-white/[0.12] text-white/15">
      <span className="text-2xl font-light leading-none">+</span>
    </div>
  );
}

export function RosterBuilder() {
  const [players, setPlayers] = useState<Player[]>([]);
  const [playersError, setPlayersError] = useState<string | null>(null);

  const [rosters, setRosters] = useState<RosterSummary[]>([]);
  const [rostersLoading, setRostersLoading] = useState(true);
  const [rostersError, setRostersError] = useState<string | null>(null);

  const [activeRoster, setActiveRoster] = useState<RosterOut | null>(null);
  const [activeError, setActiveError] = useState<string | null>(null);

  const [builderName, setBuilderName] = useState("");
  const [builderPlayerIds, setBuilderPlayerIds] = useState<number[]>([]);
  const [builderSearch, setBuilderSearch] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const [manageSearch, setManageSearch] = useState("");

  useEffect(() => {
    fetch(`${API_BASE}/players?limit=1000`)
      .then((res) => res.json())
      .then((result: Player[]) => setPlayers(result))
      .catch(() => setPlayersError("Couldn't load player data."));
  }, []);

  function refreshRosters() {
    setRostersLoading(true);
    fetch(`${API_BASE}/rosters`)
      .then((res) => res.json())
      .then((result: RosterSummary[]) => {
        setRostersError(null);
        setRosters(result);
      })
      .catch(() => setRostersError("Couldn't load saved rosters."))
      .finally(() => setRostersLoading(false));
  }

  useEffect(() => {
    refreshRosters();
  }, []);

  const dedupedPlayers = useMemo(() => {
    const seen = new Set<number>();
    return players.filter((p) => {
      if (seen.has(p.player_id)) return false;
      seen.add(p.player_id);
      return true;
    });
  }, [players]);

  const builderSelected = useMemo(
    () => builderPlayerIds.map((id) => dedupedPlayers.find((p) => p.player_id === id)).filter(Boolean) as Player[],
    [builderPlayerIds, dedupedPlayers]
  );

  const builderResults = useMemo(() => {
    const q = builderSearch.trim().toLowerCase();
    if (!q) return [];
    return dedupedPlayers
      .filter(
        (p) =>
          !builderPlayerIds.includes(p.player_id) &&
          (p.full_name.toLowerCase().includes(q) || p.team.toLowerCase().includes(q))
      )
      .slice(0, 8);
  }, [builderSearch, dedupedPlayers, builderPlayerIds]);

  const manageResults = useMemo(() => {
    const q = manageSearch.trim().toLowerCase();
    if (!q || !activeRoster) return [];
    const onRoster = new Set(activeRoster.players.map((p) => p.player_id));
    return dedupedPlayers
      .filter(
        (p) =>
          !onRoster.has(p.player_id) &&
          (p.full_name.toLowerCase().includes(q) || p.team.toLowerCase().includes(q))
      )
      .slice(0, 8);
  }, [manageSearch, dedupedPlayers, activeRoster]);

  function addToBuilder(playerId: number) {
    if (builderPlayerIds.length >= MAX_ROSTER_SIZE) return;
    setBuilderPlayerIds((ids) => [...ids, playerId]);
    setBuilderSearch("");
  }

  function removeFromBuilder(playerId: number) {
    setBuilderPlayerIds((ids) => ids.filter((id) => id !== playerId));
  }

  async function saveRoster() {
    if (!builderName.trim() || builderPlayerIds.length < MIN_ROSTER_SIZE) return;
    setSaving(true);
    setSaveError(null);
    try {
      const res = await fetch(`${API_BASE}/rosters`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: builderName.trim(), player_ids: builderPlayerIds }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail ?? `Request failed: ${res.status}`);
      }
      setBuilderName("");
      setBuilderPlayerIds([]);
      setBuilderSearch("");
      refreshRosters();
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Couldn't save roster.");
    } finally {
      setSaving(false);
    }
  }

  async function openRoster(id: number) {
    setActiveError(null);
    setManageSearch("");
    try {
      const res = await fetch(`${API_BASE}/rosters/${id}`);
      if (!res.ok) throw new Error(`Request failed: ${res.status}`);
      setActiveRoster(await res.json());
    } catch {
      setActiveError("Couldn't load roster.");
    }
  }

  async function deleteRoster(id: number) {
    try {
      const res = await fetch(`${API_BASE}/rosters/${id}`, { method: "DELETE" });
      if (!res.ok && res.status !== 204) throw new Error(`Request failed: ${res.status}`);
      if (activeRoster?.id === id) setActiveRoster(null);
      refreshRosters();
    } catch {
      setRostersError("Couldn't delete roster.");
    }
  }

  async function addPlayerToActive(playerId: number) {
    if (!activeRoster) return;
    setActiveError(null);
    try {
      const res = await fetch(`${API_BASE}/rosters/${activeRoster.id}/players`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ player_id: playerId }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail ?? `Request failed: ${res.status}`);
      }
      setActiveRoster(await res.json());
      setManageSearch("");
      refreshRosters();
    } catch (err) {
      setActiveError(err instanceof Error ? err.message : "Couldn't add player.");
    }
  }

  async function removePlayerFromActive(playerId: number) {
    if (!activeRoster) return;
    setActiveError(null);
    try {
      const res = await fetch(`${API_BASE}/rosters/${activeRoster.id}/players/${playerId}`, {
        method: "DELETE",
      });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail ?? `Request failed: ${res.status}`);
      }
      setActiveRoster(await res.json());
      refreshRosters();
    } catch (err) {
      setActiveError(err instanceof Error ? err.message : "Couldn't remove player.");
    }
  }

  return (
    <div className="px-10 py-6">
      <h1 className="mb-1 text-2xl font-semibold text-white">Build a Roster</h1>
      <p className="mb-6 text-sm text-white/40">
        Pick {MIN_ROSTER_SIZE}–{MAX_ROSTER_SIZE} players, save the roster, and track its total salary.
      </p>

      {/* Builder */}
      <div className="mb-8 rounded-2xl border border-white/[0.08] bg-[#131418] p-6 shadow-xl shadow-black/40">
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <input
            type="text"
            value={builderName}
            onChange={(e) => setBuilderName(e.target.value)}
            placeholder="Roster name…"
            className="w-full max-w-xs rounded-lg border border-white/[0.08] bg-[#1a1b20] px-3.5 py-2 text-sm text-white placeholder:text-white/40 outline-none focus:border-white/20"
          />
          <span className="text-xs text-white/40">
            {builderPlayerIds.length}/{MAX_ROSTER_SIZE} players (min {MIN_ROSTER_SIZE})
          </span>
        </div>

        <div className="relative mb-4 max-w-sm">
          <input
            type="text"
            value={builderSearch}
            onChange={(e) => setBuilderSearch(e.target.value)}
            placeholder={
              builderPlayerIds.length >= MAX_ROSTER_SIZE ? "Roster full" : "Search players to add…"
            }
            disabled={builderPlayerIds.length >= MAX_ROSTER_SIZE}
            className="w-full rounded-lg border border-white/[0.08] bg-[#1a1b20] px-3.5 py-2 text-sm text-white placeholder:text-white/40 outline-none focus:border-white/20 disabled:opacity-40"
          />
          {builderResults.length > 0 && (
            <div className="absolute z-10 mt-1 w-full overflow-hidden rounded-lg border border-white/[0.08] bg-[#1a1b20] shadow-xl">
              {builderResults.map((p) => (
                <button
                  key={p.player_id}
                  type="button"
                  onClick={() => addToBuilder(p.player_id)}
                  className="flex w-full items-center justify-between px-3.5 py-2 text-left text-sm text-white hover:bg-white/[0.06]"
                >
                  <span>
                    {p.full_name} <span className="text-white/40">· {p.team}</span>
                  </span>
                  <span className="text-white/50">{formatSalary(p.salary)}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {playersError && <p className="mb-4 text-sm text-[#FF5000]">{playersError}</p>}

        <div className="mb-4 grid grid-cols-3 gap-3 sm:grid-cols-4 lg:grid-cols-5">
          {builderSelected.map((p) => (
            <PlayerSlot
              key={p.player_id}
              name={p.full_name}
              position={p.position}
              team={p.team}
              salary={p.salary}
              onRemove={() => removeFromBuilder(p.player_id)}
            />
          ))}
          {Array.from({ length: Math.max(0, MAX_ROSTER_SIZE - builderSelected.length) }).map((_, i) => (
            <EmptySlot key={`empty-${i}`} />
          ))}
        </div>

        <div className="flex items-center justify-between border-t border-white/[0.08] pt-4">
          <div>
            <div className="text-xs font-medium text-white/40">Total salary</div>
            <div className="font-mono text-xl font-semibold tabular-nums text-white">
              {formatSalary(totalOf(builderSelected))}
            </div>
          </div>
          <div className="flex items-center gap-3">
            {saveError && <span className="text-sm text-[#FF5000]">{saveError}</span>}
            {!saveError && builderPlayerIds.length > 0 && builderPlayerIds.length < MIN_ROSTER_SIZE && (
              <span className="text-sm text-white/40">
                Need {MIN_ROSTER_SIZE - builderPlayerIds.length} more player
                {MIN_ROSTER_SIZE - builderPlayerIds.length === 1 ? "" : "s"}
              </span>
            )}
            <button
              type="button"
              onClick={saveRoster}
              disabled={saving || !builderName.trim() || builderPlayerIds.length < MIN_ROSTER_SIZE}
              className="rounded-lg bg-[#00C805] px-4 py-2 text-sm font-semibold text-black hover:bg-[#00b304] disabled:cursor-not-allowed disabled:opacity-30"
            >
              {saving ? "Saving…" : "Save Roster"}
            </button>
          </div>
        </div>
      </div>

      {/* Saved rosters */}
      <h2 className="mb-3 text-base font-semibold text-white">Saved Rosters</h2>

      {rostersLoading && <p className="text-sm text-white/40">Loading rosters…</p>}
      {rostersError && <p className="text-sm text-[#FF5000]">{rostersError}</p>}

      {!rostersLoading && rosters.length === 0 && (
        <p className="text-sm text-white/40">No saved rosters yet.</p>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {rosters.map((r) => (
          <div
            key={r.id}
            className="rounded-2xl border border-white/[0.08] bg-[#131418] p-5 shadow-xl shadow-black/40"
          >
            <div className="mb-3 flex items-start justify-between">
              <div>
                <div className="font-semibold text-white">{r.name}</div>
                <div className="text-xs text-white/40">
                  {r.player_count}/{MAX_ROSTER_SIZE} players
                </div>
              </div>
              <button
                type="button"
                onClick={() => deleteRoster(r.id)}
                className="rounded-lg border border-white/[0.08] px-2.5 py-1 text-xs font-medium text-white/50 hover:border-[#FF5000]/40 hover:text-[#FF5000]"
              >
                Delete
              </button>
            </div>
            <div className="mb-3 font-mono text-lg font-semibold tabular-nums text-white">
              {formatSalary(r.total_salary)}
            </div>
            <button
              type="button"
              onClick={() => openRoster(r.id)}
              className="w-full rounded-lg border border-white/[0.08] py-1.5 text-sm font-medium text-white/70 hover:bg-white/[0.06]"
            >
              Manage
            </button>
          </div>
        ))}
      </div>

      {/* Manage panel */}
      {activeRoster && (
        <div className="fixed inset-0 z-20 flex items-center justify-center bg-black/60 px-4">
          <div className="max-h-[85vh] w-full max-w-3xl overflow-y-auto rounded-2xl border border-white/[0.08] bg-[#131418] p-8 shadow-2xl">
            <div className="mb-6 flex items-center justify-between">
              <div>
                <h3 className="text-2xl font-semibold text-white">{activeRoster.name}</h3>
                <p className="mt-1 text-sm text-white/40">
                  {activeRoster.players.length}/{MAX_ROSTER_SIZE} players
                </p>
              </div>
              <button
                type="button"
                onClick={() => setActiveRoster(null)}
                className="flex h-8 w-8 items-center justify-center rounded-full text-xl text-white/40 hover:bg-white/[0.06] hover:text-white"
                aria-label="Close"
              >
                ×
              </button>
            </div>

            {activeError && <p className="mb-3 text-sm text-[#FF5000]">{activeError}</p>}

            <div className="relative mb-5 max-w-sm">
              <input
                type="text"
                value={manageSearch}
                onChange={(e) => setManageSearch(e.target.value)}
                placeholder={
                  activeRoster.players.length >= MAX_ROSTER_SIZE
                    ? "Roster full"
                    : "Add a player…"
                }
                disabled={activeRoster.players.length >= MAX_ROSTER_SIZE}
                className="w-full rounded-lg border border-white/[0.08] bg-[#1a1b20] px-3.5 py-2 text-sm text-white placeholder:text-white/40 outline-none focus:border-white/20 disabled:opacity-40"
              />
              {manageResults.length > 0 && (
                <div className="absolute z-10 mt-1 w-full overflow-hidden rounded-lg border border-white/[0.08] bg-[#1a1b20] shadow-xl">
                  {manageResults.map((p) => (
                    <button
                      key={p.player_id}
                      type="button"
                      onClick={() => addPlayerToActive(p.player_id)}
                      className="flex w-full items-center justify-between px-3.5 py-2 text-left text-sm text-white hover:bg-white/[0.06]"
                    >
                      <span>
                        {p.full_name} <span className="text-white/40">· {p.team}</span>
                      </span>
                      <span className="text-white/50">{formatSalary(p.salary)}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="mb-6 grid grid-cols-3 gap-3 sm:grid-cols-4 lg:grid-cols-5">
              {activeRoster.players.map((p) => (
                <PlayerSlot
                  key={p.player_id}
                  name={p.full_name}
                  position={p.position}
                  team={p.team}
                  salary={p.salary}
                  onRemove={() => removePlayerFromActive(p.player_id)}
                />
              ))}
              {Array.from({ length: Math.max(0, MAX_ROSTER_SIZE - activeRoster.players.length) }).map((_, i) => (
                <EmptySlot key={`empty-${i}`} />
              ))}
            </div>

            <div className="flex items-center justify-between border-t border-white/[0.08] pt-4">
              <div>
                <div className="text-xs font-medium text-white/40">Total salary</div>
                <div className="font-mono text-lg font-semibold tabular-nums text-white">
                  {formatSalary(activeRoster.total_salary)}
                </div>
              </div>
              <button
                type="button"
                onClick={() => deleteRoster(activeRoster.id)}
                className="rounded-lg border border-white/[0.08] px-3 py-1.5 text-sm font-medium text-white/50 hover:border-[#FF5000]/40 hover:text-[#FF5000]"
              >
                Delete Roster
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
