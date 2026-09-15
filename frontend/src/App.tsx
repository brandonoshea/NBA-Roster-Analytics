import { useEffect, useState } from 'react'
import PlayerTable, { type PlayerSeason } from './components/PlayerTable'

function App() {
  const [players, setPlayers] = useState<PlayerSeason[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/players?limit=50')
      .then((res) => {
        if (!res.ok) throw new Error(`Request failed: ${res.status}`)
        return res.json()
      })
      .then(setPlayers)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="min-h-svh bg-[var(--bg)] px-4 py-10 sm:px-8">
      <div className="mx-auto max-w-5xl">
        <div className="mb-6">
          <h1>NBA Roster Analytics</h1>
          <p className="mt-1 text-sm text-[var(--text-dim)]">
            Player salary valuations · 2026 season
          </p>
        </div>

        {loading && <p className="text-[var(--text-dim)]">Loading players…</p>}
        {error && <p className="text-[var(--down)]">{error}</p>}

        {!loading && !error && <PlayerTable players={players} />}
      </div>
    </div>
  )
}

export default App
