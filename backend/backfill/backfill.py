"""
Backfill salary data (2014-2026) into Postgres.

Scope, deliberately: SALARY ONLY. No stats, no FastAPI, no frontend.
Goal: player_seasons rows exist, salary populated, stats left null,
matched correctly to a single Player row via bref_id (not name).

Run once, manually, from backend/ (as a module, so db/models/core resolve):
    python -m backfill.backfill
"""

import time
import random
import logging
from pathlib import Path

import requests
from bs4 import BeautifulSoup, Comment

from db.database import SessionLocal, create_tables
from models.salary import Player, PlayerSeason

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

TEAMS = [
    "ATL", "BOS", "BRK", "CHO", "CHI", "CLE", "DAL", "DEN", "DET", "GSW",
    "HOU", "IND", "LAC", "LAL", "MEM", "MIA", "MIL", "MIN", "NOP", "NYK",
    "OKC", "ORL", "PHI", "PHO", "POR", "SAC", "SAS", "TOR", "UTA", "WAS",
]

YEARS = range(2014, 2027)

# Charlotte rebranded Bobcats -> Hornets for the 2014-15 season; basketball-reference
# keeps the old "CHA" code only for 2014, "CHO" for every season since.
def _bref_team_code(team: str, year: int) -> str:
    if team == "CHO" and year == 2014:
        return "CHA"
    return team

CACHE_DIR = Path("cache/html")
REQUEST_DELAY_RANGE = (2.0, 4.0)
MAX_RETRIES = 3

HEADERS = {
    "User-Agent": "Mozilla/5.0 (personal research project; contact: your_email@example.com)"
}

session = requests.Session()
session.headers.update(HEADERS)


def fetch_html(team: str, year: int) -> str | None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / f"{team}_{year}.html"

    if cache_path.exists():
        return cache_path.read_text(encoding="utf-8")

    url = f"https://www.basketball-reference.com/teams/{_bref_team_code(team, year)}/{year}.html"

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = session.get(url, timeout=10)
            if resp.status_code == 200:
                resp.encoding = "utf-8"  # bref sends no charset header; requests mis-guesses ISO-8859-1 and mangles accented names
                cache_path.write_text(resp.text, encoding="utf-8")
                return resp.text
            elif resp.status_code == 429:
                wait = 30 * attempt
                log.warning(f"Rate limited on {team} {year}, waiting {wait}s")
                time.sleep(wait)
            else:
                log.warning(f"{team} {year} returned status {resp.status_code}")
                return None
        except requests.RequestException as e:
            log.warning(f"Request error for {team} {year} (attempt {attempt}): {e}")
            time.sleep(5 * attempt)

    log.error(f"Giving up on {team} {year} after {MAX_RETRIES} attempts")
    return None


def extract_salary_rows(html: str, team: str, year: int) -> list[dict]:
    """
    Parse the salaries2 table out of the HTML comment, pulling player name,
    bref_id (from the href, not the display text), and salary for each row.
    """
    soup = BeautifulSoup(html, "html.parser")
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))

    for c in comments:
        if 'id="salaries2"' in c:
            comment_soup = BeautifulSoup(c, "html.parser")
            table = comment_soup.find("table", {"id": "salaries2"})
            if not table:
                continue

            rows = []
            for tr in table.find("tbody").find_all("tr"):
                player_cell = tr.find("td", {"data-stat": "player"})
                salary_cell = tr.find("td", {"data-stat": "salary"})
                if player_cell is None or salary_cell is None:
                    continue

                link = player_cell.find("a")
                if link is None or "href" not in link.attrs:
                    continue

                # href looks like /players/j/jamesle01.html -> bref_id = jamesle01
                bref_id = link["href"].split("/")[-1].replace(".html", "")
                full_name = player_cell.get_text(strip=True)

                salary_text = salary_cell.get_text(strip=True)
                salary = _parse_salary(salary_text)
                if salary is None:
                    continue

                rows.append({
                    "full_name": full_name,
                    "bref_id": bref_id,
                    "salary": salary,
                    "team": team,
                    "season": year,
                })
            return rows

    log.info(f"No salary table found for {team} {year} (may not have existed that season)")
    return []


def _parse_salary(text: str) -> float | None:
    cleaned = text.replace("$", "").replace(",", "").strip()
    if not cleaned or not cleaned.isdigit():
        return None
    return float(cleaned)


def get_or_create_player(db, full_name: str, bref_id: str) -> Player:
    """
    The core integrity step: match on bref_id, NOT name, since names collide
    (multiple real players can share a name) but bref_id is guaranteed unique.
    """
    player = db.query(Player).filter(Player.bref_id == bref_id).first()
    if player:
        return player

    player = Player(full_name=full_name, bref_id=bref_id)
    db.add(player)
    db.flush()  # assigns player.id without committing the whole transaction yet
    return player


def upsert_player_season(db, player: Player, row: dict):
    """
    Insert if this (player_id, season, team) doesn't exist yet.
    Update salary if it does (idempotent - safe to rerun).
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
        existing.salary = row["salary"]
    else:
        db.add(PlayerSeason(
            player_id=player.id,
            season=row["season"],
            team=row["team"],
            salary=row["salary"],
        ))
        # Flush so a duplicate row later in the same team/year batch (bref
        # sometimes lists a waived-and-re-signed player twice) is caught by
        # the existing-check above instead of hitting the unique constraint.
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

                html = fetch_html(team, year)
                if html is None:
                    continue

                rows = extract_salary_rows(html, team, year)

                for row in rows:
                    player = get_or_create_player(db, row["full_name"], row["bref_id"])
                    upsert_player_season(db, player, row)
                    rows_written += 1

                db.commit()  # commit per team/year - crash-safe, resumable
                time.sleep(random.uniform(*REQUEST_DELAY_RANGE))

    finally:
        db.close()

    log.info(f"Done. {rows_written} player-season rows written/updated.")


if __name__ == "__main__":
    main()