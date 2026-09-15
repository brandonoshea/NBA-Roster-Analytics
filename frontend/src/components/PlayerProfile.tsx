import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

// Decimal fields come back from FastAPI as numeric strings, not JSON numbers.
type Numeric = number | string | null

interface PlayerSeasonDetail {
  player_id: number
  full_name: string
  season: number
  team: string
  position: string | null
  headshot_url: string | null
  salary: Numeric
  points: Numeric
  rebounds: Numeric
  assists: Numeric
  games_played: number | null
  games_started: number | null
  minutes_played: Numeric
  per: Numeric
  true_shooting_pct: Numeric
  usage_pct: Numeric
  win_shares: Numeric
  box_plus_minus: Numeric
  vorp: Numeric
  predicted_salary: Numeric
  verdict: string | null
  delta_pct: Numeric
}

const currency = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
})

function formatSalary(value: Numeric) {
  return value == null ? '—' : currency.format(Number(value))
}

function formatStat(value: Numeric, digits = 1) {
  return value == null ? '—' : Number(value).toFixed(digits)
}

function formatDelta(value: Numeric) {
  if (value == null) return null
  const n = Number(value)
  const sign = n > 0 ? '+' : ''
  return `${sign}${n.toFixed(1)}%`
}

function verdictBadge(verdict: string | null) {
  if (verdict === 'Overpaid') {
    return 'bg-[var(--down-bg)] text-[var(--down)]'
  }
  if (verdict === 'Underpaid') {
    return 'bg-[var(--up-bg)] text-[var(--up)]'
  }
  return 'bg-[var(--surface-hover)] text-[var(--text-dim)]'
}

function deltaColor(value: Numeric) {
  if (value == null) return 'text-[var(--text-dim)]'
  const n = Number(value)
  if (n > 0) return 'text-[var(--down)]'
  if (n < 0) return 'text-[var(--up)]'
  return 'text-[var(--text-dim)]'
}

interface StatTileProps {
  label: string
  value: string
}

function StatTile({ label, value }: StatTileProps) {
  return (
    <div className="flex-1 rounded-xl border border-[var(--border)] bg-[var(--surface)] px-4 py-3 text-center">
      <div className="font-mono text-2xl font-semibold tabular-nums">{value}</div>
      <div className="mt-1 text-xs font-medium text-[var(--text-dim)]">{label}</div>
    </div>
  )
}

function PlayerProfile() {
  const { playerId } = useParams()
  const [seasons, setSeasons] = useState<PlayerSeasonDetail[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    fetch(`/api/players/${playerId}`)
      .then((res) => {
        if (!res.ok) throw new Error(`Request failed: ${res.status}`)
        return res.json()
      })
      .then(setSeasons)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [playerId])

  const latest = seasons[0]

  return (
    <div className="min-h-svh bg-[var(--bg)] px-4 py-10 sm:px-8">
      <div className="mx-auto max-w-5xl">
        <Link
          to="/"
          className="mb-6 inline-block text-sm text-[var(--text-dim)] hover:text-[var(--text)]"
        >
          ← Back to players
        </Link>

        {loading && <p className="text-[var(--text-dim)]">Loading player…</p>}
        {error && <p className="text-[var(--down)]">{error}</p>}

        {!loading && !error && latest && (
          <>
            <div className="mb-6 flex items-center gap-5">
              {latest.headshot_url && (
                <img
                  src={latest.headshot_url}
                  alt={latest.full_name}
                  className="h-32 w-32 rounded-2xl border border-[var(--border)] bg-[var(--surface)] object-contain"
                />
              )}
              <div>
                <h1 className="text-3xl">{latest.full_name}</h1>
                <p className="mt-1 text-sm text-[var(--text-dim)]">
                  {latest.position ?? '—'} · {latest.team} · {latest.season} season
                </p>
              </div>
            </div>

            <div className="mb-3 flex gap-3">
              <StatTile label="PTS" value={formatStat(latest.points)} />
              <StatTile label="REB" value={formatStat(latest.rebounds)} />
              <StatTile label="AST" value={formatStat(latest.assists)} />
              <StatTile label="GP" value={latest.games_played?.toString() ?? '—'} />
            </div>

            <div className="mb-6 flex flex-col gap-5 rounded-xl border border-[var(--border)] bg-[var(--surface)] px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex flex-wrap items-center gap-x-12 gap-y-4">
                <div>
                  <div className="text-sm font-medium text-[var(--text-dim)]">
                    Current salary
                  </div>
                  <div className="font-mono text-3xl font-semibold tabular-nums">
                    {formatSalary(latest.salary)}
                  </div>
                </div>
                <div>
                  <div className="text-sm font-medium text-[var(--text-dim)]">
                    Predicted salary
                  </div>
                  <div className="font-mono text-3xl font-semibold tabular-nums text-[var(--text-dim)]">
                    {formatSalary(latest.predicted_salary)}
                  </div>
                </div>
                {latest.delta_pct != null && (
                  <div>
                    <div className="text-sm font-medium text-[var(--text-dim)]">Δ</div>
                    <div
                      className={`font-mono text-3xl font-semibold tabular-nums ${deltaColor(latest.delta_pct)}`}
                    >
                      {formatDelta(latest.delta_pct)}
                    </div>
                  </div>
                )}
              </div>
              {latest.verdict && (
                <span
                  className={`inline-block w-fit rounded-full px-4 py-2 text-base font-medium ${verdictBadge(latest.verdict)}`}
                >
                  {latest.verdict}
                </span>
              )}
            </div>

            <h2 className="mb-3 text-base">
              Season History{' '}
              <span className="text-sm font-normal text-[var(--text-dim)]">
                · last {seasons.length} season{seasons.length === 1 ? '' : 's'}
              </span>
            </h2>

            <div className="overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--surface)]">
              <table className="w-full border-collapse text-left text-[13px]">
                <thead>
                  <tr className="border-b border-[var(--border)] text-[var(--text-dim)]">
                    <th className="py-3 pl-5 pr-3 font-medium">Season</th>
                    <th className="px-3 py-3 font-medium">Team</th>
                    <th className="px-3 py-3 text-right font-medium">GP</th>
                    <th className="px-3 py-3 text-right font-medium">PTS</th>
                    <th className="px-3 py-3 text-right font-medium">REB</th>
                    <th className="px-3 py-3 text-right font-medium">AST</th>
                    <th className="py-3 pl-3 pr-5 text-right font-medium">Salary</th>
                  </tr>
                </thead>
                <tbody>
                  {seasons.map((s) => (
                    <tr
                      key={`${s.season}-${s.team}`}
                      className="border-b border-[var(--border)] last:border-0"
                    >
                      <td className="py-3 pl-5 pr-3 font-medium">{s.season}</td>
                      <td className="px-3 py-3 text-[var(--text-dim)]">{s.team}</td>
                      <td className="px-3 py-3 text-right font-mono tabular-nums">
                        {s.games_played ?? '—'}
                      </td>
                      <td className="px-3 py-3 text-right font-mono tabular-nums">
                        {formatStat(s.points)}
                      </td>
                      <td className="px-3 py-3 text-right font-mono tabular-nums">
                        {formatStat(s.rebounds)}
                      </td>
                      <td className="px-3 py-3 text-right font-mono tabular-nums">
                        {formatStat(s.assists)}
                      </td>
                      <td className="py-3 pl-3 pr-5 text-right font-mono tabular-nums">
                        {formatSalary(s.salary)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default PlayerProfile
