import { useNavigate } from 'react-router-dom'

// Decimal fields come back from FastAPI as numeric strings, not JSON numbers.
type Numeric = number | string | null

export interface PlayerSeason {
  player_id: number
  full_name: string
  season: number
  team: string
  salary: Numeric
  points: Numeric
  rebounds: Numeric
  assists: Numeric
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

function formatStat(value: Numeric) {
  return value == null ? '—' : Number(value).toFixed(1)
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

interface PlayerTableProps {
  players: PlayerSeason[]
}

function PlayerTable({ players }: PlayerTableProps) {
  const navigate = useNavigate()

  return (
    <div className="overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--surface)]">
      <table className="w-full border-collapse text-left text-[13px]">
        <thead>
          <tr className="border-b border-[var(--border)] text-[var(--text-dim)]">
            <th className="py-3 pl-5 pr-3 font-medium">Player</th>
            <th className="px-3 py-3 font-medium">Team</th>
            <th className="px-3 py-3 text-right font-medium">PTS</th>
            <th className="px-3 py-3 text-right font-medium">REB</th>
            <th className="px-3 py-3 text-right font-medium">AST</th>
            <th className="px-3 py-3 text-right font-medium">Salary</th>
            <th className="px-3 py-3 text-right font-medium">Predicted</th>
            <th className="px-3 py-3 text-right font-medium">Δ</th>
            <th className="py-3 pl-3 pr-5 font-medium">Verdict</th>
          </tr>
        </thead>
        <tbody>
          {players.map((p) => (
            <tr
              key={`${p.player_id}-${p.team}`}
              onClick={() => navigate(`/players/${p.player_id}`)}
              className="cursor-pointer border-b border-[var(--border)] last:border-0 transition-colors hover:bg-[var(--surface-hover)]"
            >
              <td className="py-3 pl-5 pr-3 font-medium">{p.full_name}</td>
              <td className="px-3 py-3 text-[var(--text-dim)]">{p.team}</td>
              <td className="px-3 py-3 text-right font-mono tabular-nums">
                {formatStat(p.points)}
              </td>
              <td className="px-3 py-3 text-right font-mono tabular-nums">
                {formatStat(p.rebounds)}
              </td>
              <td className="px-3 py-3 text-right font-mono tabular-nums">
                {formatStat(p.assists)}
              </td>
              <td className="px-3 py-3 text-right font-mono tabular-nums">
                {formatSalary(p.salary)}
              </td>
              <td className="px-3 py-3 text-right font-mono tabular-nums text-[var(--text-dim)]">
                {formatSalary(p.predicted_salary)}
              </td>
              <td
                className={`px-3 py-3 text-right font-mono tabular-nums ${deltaColor(p.delta_pct)}`}
              >
                {formatDelta(p.delta_pct) ?? '—'}
              </td>
              <td className="py-3 pl-3 pr-5">
                {p.verdict && (
                  <span
                    className={`inline-block rounded-full px-2.5 py-1 text-xs font-medium ${verdictBadge(p.verdict)}`}
                  >
                    {p.verdict}
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default PlayerTable
