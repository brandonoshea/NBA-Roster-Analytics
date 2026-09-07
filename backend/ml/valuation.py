"""
Score every player's most recent season with the trained XGBoost model
(ml/train_valuation.py) and upsert the result into player_valuations:
predicted salary, the actual salary, and an over/underpaid verdict.

Only scores each player's latest season, since player_valuations has a
unique constraint on player_id (one current valuation per player, not one
per season).

Run after ml/train_valuation.py has produced ml/artifacts/xgb_valuation.joblib,
manually, from backend/ (as a module, so db/models/core resolve):
    python -m ml.valuation
"""

import logging

import joblib
import numpy as np
import pandas as pd
from sqlalchemy import func

from db.database import SessionLocal, create_tables
from models.salary import Player, PlayerSeason
from models.valuation import PlayerValuation
from ml.train_valuation import ARTIFACT_PATH, FEATURES

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# |delta_pct| below this is "Fair Value"; above it, over/underpaid.
FAIR_VALUE_BAND_PCT = 15.0

# Minimum games in a season for it to count as a player's "latest season" --
# filters out injury/inactive token appearances that would otherwise be
# scored against a full-season salary.
MIN_GAMES_PLAYED = 15


def load_latest_seasons(db) -> pd.DataFrame:
    """
    Each player's most recent season row that has the stats the model
    needs. Salary may be missing (e.g. a player about to sign an extension)
    -- those rows still get a predicted_salary, just no actual/verdict.
    """
    # Require a real sample of games -- otherwise an injury-shortened or
    # end-of-career token appearance becomes a player's "latest season" and
    # produces a near-zero predicted salary against a full guaranteed
    # contract, swamping the over/underpaid ranking with noise.
    latest_season_subq = (
        db.query(
            PlayerSeason.player_id,
            func.max(PlayerSeason.season).label("season"),
        )
        .filter(PlayerSeason.points.isnot(None))
        .filter(PlayerSeason.per.isnot(None))
        .filter(PlayerSeason.games_played >= MIN_GAMES_PLAYED)
        .group_by(PlayerSeason.player_id)
        .subquery()
    )

    rows = (
        db.query(PlayerSeason, Player.full_name)
        .join(Player, Player.id == PlayerSeason.player_id)
        .join(
            latest_season_subq,
            (PlayerSeason.player_id == latest_season_subq.c.player_id)
            & (PlayerSeason.season == latest_season_subq.c.season),
        )
        .all()
    )

    records = []
    for season_row, full_name in rows:
        record = {
            "player_id": season_row.player_id,
            "full_name": full_name,
            "season": season_row.season,
            "salary": season_row.salary,
        }
        for col in FEATURES:
            if col != "season":
                record[col] = getattr(season_row, col)
        records.append(record)

    df = pd.DataFrame.from_records(records)

    # A player traded mid-season has one PlayerSeason row per team for that
    # same max season; keep the stint with the most minutes as the
    # representative row, but take salary from whichever row has it (bref
    # doesn't consistently repeat it on both team rows).
    df["minutes_played"] = pd.to_numeric(df["minutes_played"], errors="coerce")
    salary_by_player = df.groupby("player_id")["salary"].apply(
        lambda s: s.dropna().iloc[0] if s.notna().any() else None
    )
    df = (
        df.sort_values("minutes_played", ascending=False)
        .drop_duplicates(subset="player_id", keep="first")
    )
    df["salary"] = df["player_id"].map(salary_by_player)

    return df


def predict(df: pd.DataFrame, model, features: list[str]) -> pd.Series:
    X = df[features].apply(pd.to_numeric, errors="coerce")
    return pd.Series(np.expm1(model.predict(X)), index=df.index)


def verdict_for(delta_pct: float) -> str:
    if delta_pct > FAIR_VALUE_BAND_PCT:
        return "Overpaid"
    if delta_pct < -FAIR_VALUE_BAND_PCT:
        return "Underpaid"
    return "Fair Value"


def upsert_valuation(db, row: pd.Series):
    existing = (
        db.query(PlayerValuation)
        .filter(PlayerValuation.player_id == row["player_id"])
        .first()
    )

    actual_salary = float(row["salary"]) if pd.notna(row["salary"]) else None
    predicted_salary = float(row["predicted_salary"])
    if actual_salary is not None and actual_salary > 0:
        delta_pct = float((actual_salary - predicted_salary) / predicted_salary * 100)
        verdict = verdict_for(delta_pct)
    else:
        delta_pct = None
        verdict = None

    if existing:
        existing.season = int(row["season"])
        existing.predicted_salary = predicted_salary
        existing.actual_salary = actual_salary
        existing.verdict = verdict
        existing.delta_pct = delta_pct
    else:
        db.add(PlayerValuation(
            player_id=row["player_id"],
            season=int(row["season"]),
            predicted_salary=predicted_salary,
            actual_salary=actual_salary,
            verdict=verdict,
            delta_pct=delta_pct,
        ))


def main():
    create_tables()

    artifact = joblib.load(ARTIFACT_PATH)
    model, features = artifact["model"], artifact["features"]

    db = SessionLocal()
    try:
        df = load_latest_seasons(db)
        log.info(f"Scoring {len(df)} players' latest seasons")

        df["predicted_salary"] = predict(df, model, features)

        for _, row in df.iterrows():
            upsert_valuation(db, row)

        db.commit()
    finally:
        db.close()

    log.info(f"Done. {len(df)} player valuations written.")


if __name__ == "__main__":
    main()
