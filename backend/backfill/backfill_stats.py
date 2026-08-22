"""
Backfill per-game stats (points, rebounds, assists) into Postgres.

Reuses the team/season pages already downloaded by backfill.py: basketball-
reference serves per-game stats and salaries on the same page, so this script
re-parses the existing cache/html/*.html files instead of re-fetching. Matches
players by bref_id and updates the existing (player_id, season, team) row from
the salary backfill; creates the row if a player has stats but never appeared
in the salaries table (e.g. two-way/10-day contracts).

Run once, manually, from backend/ (as a module, so db/models/core resolve):
    python -m backfill.backfill_stats
"""

import time
import random
import logging

from bs4 import BeautifulSoup

from db.database import SessionLocal, create_tables
from models.salary import PlayerSeason
from backfill.backfill import (
    TEAMS, YEARS, CACHE_DIR, REQUEST_DELAY_RANGE,
    fetch_html, get_or_create_player,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def extract_stat_rows(html: str, team: str, year: int) -> list[dict]:
    """
    Parse the per_game_stats table (unlike salaries2, this one isn't wrapped
    in an HTML comment) for player name, bref_id, and per-game pts/reb/ast.
    """
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", {"id": "per_game_stats"})
    if table is None:
        log.info(f"No per-game stats table found for {team} {year}")
        return []

    rows = []
    for tr in table.find("tbody").find_all("tr"):
        name_cell = tr.find("td", {"data-stat": "name_display"})
        if name_cell is None:
            continue

        link = name_cell.find("a")
        if link is None or "href" not in link.attrs:
            continue  # e.g. the "Team Totals" row has no player link

        # href looks like /players/t/tatumja01.html -> bref_id = tatumja01
        bref_id = link["href"].split("/")[-1].replace(".html", "")
        full_name = name_cell.get_text(strip=True)

        points = _parse_stat(tr, "pts_per_g")
        rebounds = _parse_stat(tr, "trb_per_g")
        assists = _parse_stat(tr, "ast_per_g")
        if points is None and rebounds is None and assists is None:
            continue

        rows.append({
            "full_name": full_name,
            "bref_id": bref_id,
            "points": points,
            "rebounds": rebounds,
            "assists": assists,
            "team": team,
            "season": year,
        })
    return rows


def _parse_stat(tr, stat: str) -> float | None:
    cell = tr.find("td", {"data-stat": stat})
    if cell is None:
        return None
    text = cell.get_text(strip=True)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def upsert_player_season_stats(db, player, row: dict):
    """
    Update stats on the matching (player_id, season, team) row from the salary
    backfill; create it if this player never showed up in the salaries table.
    """
    existing = (
        db.query(PlayerSeason)
        .filter(
            PlayerSeason.player_id == player.id,
            PlayerSeason.season == row["season"],
            PlayerSeason.team == row["team"],
        )
        .first()
    )

    if existing:
        existing.points = row["points"]
        existing.rebounds = row["rebounds"]
        existing.assists = row["assists"]
    else:
        db.add(PlayerSeason(
            player_id=player.id,
            season=row["season"],
            team=row["team"],
            points=row["points"],
            rebounds=row["rebounds"],
            assists=row["assists"],
        ))
        db.flush()


def main():
    create_tables()

    total = len(TEAMS) * len(list(YEARS))
    done = 0
    rows_written = 0

    db = SessionLocal()

    try:
        for team in TEAMS:
            for year in YEARS:
                done += 1
                log.info(f"[{done}/{total}] {team} {year}")

                cache_path = CACHE_DIR / f"{team}_{year}.html"
                was_cached = cache_path.exists()

                html = fetch_html(team, year)
                if html is None:
                    continue

                rows = extract_stat_rows(html, team, year)

                for row in rows:
                    player = get_or_create_player(db, row["full_name"], row["bref_id"])
                    upsert_player_season_stats(db, player, row)
                    rows_written += 1

                db.commit()  # commit per team/year - crash-safe, resumable

                if not was_cached:
                    time.sleep(random.uniform(*REQUEST_DELAY_RANGE))

    finally:
        db.close()

    log.info(f"Done. {rows_written} player-season rows updated with stats.")


if __name__ == "__main__":
    main()
