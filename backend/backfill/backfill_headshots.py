"""
Backfill player headshot image URLs into Postgres.

Scope, deliberately: HEADSHOTS ONLY, keyed off bref_id. Unlike backfill.py's
siblings (backfill_stats.py, backfill_advanced.py), this doesn't reuse the
team/season cache pages - headshots live on each player's own bref page, one
fetch per player instead of one per team/year. Existing players (already
loaded by backfill.py) are read from the DB; each player's page is fetched
(cached) and the headshot <img src> is extracted directly, since bref rotates
a cache-version path segment (req/<number>/) site-wide that isn't tied to the
player and shouldn't be reconstructed by hand.

Run once, manually, from backend/ (as a module, so db/models/core resolve):
    python -m backfill.backfill_headshots
"""

import time
import random
import logging
from pathlib import Path

from bs4 import BeautifulSoup
from sqlalchemy import text

from db.database import SessionLocal, create_tables, engine
from models.salary import Player
from backfill.backfill import REQUEST_DELAY_RANGE, fetch_page

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

PLAYER_CACHE_DIR = Path("cache/html/players")


def ensure_headshot_column():
    """
    No Alembic in this project - the players table already exists from an
    earlier create_tables() run, so Base.metadata.create_all() won't add a
    new column to it. Add it directly; safe to rerun.
    """
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE players ADD COLUMN IF NOT EXISTS headshot_url VARCHAR"))


def fetch_player_html(bref_id: str) -> str | None:
    cache_path = PLAYER_CACHE_DIR / f"{bref_id}.html"
    url = f"https://www.basketball-reference.com/players/{bref_id[0]}/{bref_id}.html"
    return fetch_page(url, cache_path)


def extract_headshot_url(html: str) -> str | None:
    """
    Match on the /headshots/ path segment rather than a specific container
    (e.g. div#meta), since that's the one part of the markup unlikely to
    change even if bref restructures the page layout.
    """
    soup = BeautifulSoup(html, "html.parser")
    img = soup.find("img", src=lambda s: s and "/headshots/" in s)
    return img["src"] if img else None


def main():
    create_tables()
    ensure_headshot_column()

    db = SessionLocal()

    try:
        players = (
            db.query(Player)
            .filter(Player.bref_id.isnot(None), Player.bref_id != "", Player.headshot_url.is_(None))
            .order_by(Player.id)
            .all()
        )

        total = len(players)
        found = 0

        for i, player in enumerate(players, start=1):
            log.info(f"[{i}/{total}] {player.full_name} ({player.bref_id})")

            cache_path = PLAYER_CACHE_DIR / f"{player.bref_id}.html"
            was_cached = cache_path.exists()

            html = fetch_player_html(player.bref_id)
            if html is None:
                continue

            headshot_url = extract_headshot_url(html)
            if headshot_url is None:
                log.info(f"No headshot found for {player.bref_id}")
            else:
                player.headshot_url = headshot_url
                found += 1

            db.commit()  # commit per player - crash-safe, resumable

            if not was_cached:
                time.sleep(random.uniform(*REQUEST_DELAY_RANGE))

    finally:
        db.close()

    log.info(f"Done. {found}/{total} players updated with a headshot URL.")


if __name__ == "__main__":
    main()
