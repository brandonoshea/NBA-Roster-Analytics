# NBA Roster Analytics

A full-stack app for exploring NBA player salaries, seeing whether a player is
over- or under-paid relative to an ML-predicted "fair" salary, and building
hypothetical rosters with live salary totals.

## Features

- **Player table** — every player's latest season, searchable and sortable by
  team, stats, salary, predicted salary, and valuation verdict.
- **Player profile** — season-by-season history for an individual player.
- **Salary valuation** — an XGBoost model trained on historical
  stats-to-salary data predicts each player's "expected" salary; players are
  tagged `Underpaid` / `Fair Value` / `Overpaid` based on the delta.
- **Roster builder** — assemble a roster (8–15 players), see its total salary
  update live, save it, and manage saved rosters (add/remove players,
  delete).

## Tech stack

| Layer    | Stack                                                                 |
| -------- | ---------------------------------------------------------------------- |
| Frontend | React 19, TypeScript, Vite, Tailwind CSS v4, React Router              |
| Backend  | FastAPI, SQLAlchemy, Pydantic v2, Postgres                             |
| ML       | scikit-learn / XGBoost, trained offline and scored into Postgres       |
| Data     | Scraped from basketball-reference.com (salaries, per-game & advanced stats, headshots) |

## Project structure

```
backend/
  main.py              FastAPI app entrypoint
  core/config.py        Settings (reads backend/.env)
  db/database.py        SQLAlchemy engine/session setup
  models/                ORM models (Player, PlayerSeason, PlayerValuation, Roster)
  schemas/                Pydantic request/response schemas
  routers/                 API routes (/players, /rosters)
  backfill/               One-off scripts that scrape & load historical data
  ml/                       Valuation model training (train_valuation.py) and scoring (valuation.py)
  tests/                    pytest suite (sqlite-backed, see tests/conftest.py)
frontend/
  src/components/        Page components (MainTable, PlayerProfile, RosterBuilder, Title)
  src/types/               Shared TS types matching backend schemas
  src/utils/format.ts     Salary/stat formatting helpers
```

## Getting started

### Prerequisites

- Python 3.11+
- Node 20+
- A local Postgres instance

### Backend

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate        # .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
```

Create `backend/.env`:

```
DATABASE_URL=postgresql://<user>:<password>@localhost:5432/nba_analytics
ALLOWED_ORIGINS=http://localhost:5173
```

Load the data (run once, in order, from `backend/`; each is slow since it
scrapes basketball-reference, but responses are cached to `backend/cache/`
so re-runs are fast):

```bash
python -m backfill.backfill            # players + salaries
python -m backfill.backfill_stats      # per-game stats
python -m backfill.backfill_advanced   # advanced stats (PER, win shares, BPM, VORP)
python -m backfill.backfill_headshots  # headshot image URLs (optional)
```

Train and score the salary valuation model:

```bash
python -m ml.train_valuation   # writes ml/artifacts/xgb_valuation.joblib
python -m ml.valuation         # scores latest seasons into player_valuations
```

Run the API (tables are created automatically on startup):

```bash
uvicorn main:app --reload
```

API docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173

## API overview

| Method | Path                               | Description                          |
| ------ | ----------------------------------- | ------------------------------------- |
| GET    | `/players`                          | Latest-season list, search/sort client-side |
| GET    | `/players/{player_id}`              | A player's season history             |
| POST   | `/rosters`                          | Create a roster (8–15 player IDs)     |
| GET    | `/rosters`                          | List saved rosters with totals        |
| GET    | `/rosters/{roster_id}`              | A roster's players + totals           |
| DELETE | `/rosters/{roster_id}`              | Delete a roster                       |
| POST   | `/rosters/{roster_id}/players`      | Add a player to a roster              |
| DELETE | `/rosters/{roster_id}/players/{player_id}` | Remove a player (blocked below 8) |

## Tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

## Known limitations

- `Player.position` exists in the schema but isn't populated by any backfill
  script yet — it's always `null`.
- `player_valuations` holds one current valuation per player, not a history,
  so there's no way to see how a prediction moved over time.
- No migration tool (e.g. Alembic) — the schema is created via
  `Base.metadata.create_all()`, so schema changes need a manual DB update or
  a fresh database.
