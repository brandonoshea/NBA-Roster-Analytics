"""
Backfill advanced stats (games, minutes, PER, TS%, usage%, win shares,
BPM, VORP) into Postgres.

Reuses the team/season pages already downloaded by backfill.py: the
"advanced" table lives on the same page as salaries and per-game stats, so
this script re-parses the existing cache/html/*.html files instead of
re-fetching. Matches players by bref_id and updates the existing
(player_id, season, team) row; creates the row if a player has advanced
stats but never appeared in the salaries or per-game tables.

Run once, manually, from backend/ (as a module, so db/models/core resolve):
    python -m backfill.backfill_advanced
"""

import time
import random
import logging

from bs4 import BeautifulSoup, Comment

from db.database import SessionLocal, create_tables
from models.salary import PlayerSeason
from backfill.backfill import (
    TEAMS, YEARS, CACHE_DIR, REQUEST_DELAY_RANGE,
    fetch_html, get_or_create_player,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# (bref data-stat name, PlayerSeason column name, python type)
STAT_FIELDS = [
    ("games", "games_played", int),
    ("games_started", "games_started", int),
    ("mp", "minutes_played", float),
    ("per", "per", float),
    ("ts_pct", "true_shooting_pct", float),
    ("usg_pct", "usage_pct", float),
    ("ows", "offensive_win_shares", float),
    ("dws", "defensive_win_shares", float),
    ("ws", "win_shares", float),
    ("ws_per_48", "win_shares_per_48", float),
    ("obpm", "offensive_bpm", float),
    ("dbpm", "defensive_bpm", float),
    ("bpm", "box_plus_minus", float),
    ("vorp", "vorp", float),
]


def extract_advanced_rows(html: str, team: str, year: int) -> list[dict]:
    """
    Parse the "advanced" table for player name, bref_id, and the
    STAT_FIELDS columns. Like salaries2 (and unlike per_game_stats), bref
    ships this table inside an HTML comment.
    """
    soup = BeautifulSoup(html, "html.parser")
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))

    table = None
    for c in comments:
        if 'id="advanced"' in c:
            comment_soup = BeautifulSoup(c, "html.parser")
            table = comment_soup.find("table", {"id": "advanced"})
            if table:
                break

    if table is None:
        log.info(f"No advanced stats table found for {team} {year}")
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

        row = {
            "full_name": full_name,
            "bref_id": bref_id,
            "team": team,
            "season": year,
        }
        has_stat = False
        for bref_stat, field, cast in STAT_FIELDS:
            value = _parse_stat(tr, bref_stat, cast)
            row[field] = value
            has_stat = has_stat or value is not None

        if not has_stat:
            continue

        rows.append(row)
    return rows


def _parse_stat(tr, stat: str, cast):
    cell = tr.find("td", {"data-stat": stat})
    if cell is None:
        return None
    text = cell.get_text(strip=True)
    if not text:
        return None
    try:
        return cast(text)
    except ValueError:
        return None


def upsert_player_season_advanced(db, player, row: dict):
    """
    Update advanced stats on the matching (player_id, season, team) row;
    create it if this player never showed up in the salary/per-game tables.
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

    field_values = {field: row[field] for _, field, _ in STAT_FIELDS}

    if existing:
        for field, value in field_values.items():
            setattr(existing, field, value)
    else:
        db.add(PlayerSeason(
            player_id=player.id,
            season=row["season"],
            team=row["team"],
            **field_values,
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

                rows = extract_advanced_rows(html, team, year)

                for row in rows:
                    player = get_or_create_player(db, row["full_name"], row["bref_id"])
                    upsert_player_season_advanced(db, player, row)
                    rows_written += 1

                db.commit()  # commit per team/year - crash-safe, resumable

                if not was_cached:
                    time.sleep(random.uniform(*REQUEST_DELAY_RANGE))

    finally:
        db.close()

    log.info(f"Done. {rows_written} player-season rows updated with advanced stats.")


if __name__ == "__main__":
    main()
