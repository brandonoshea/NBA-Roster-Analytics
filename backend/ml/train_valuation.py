"""
Train an XGBoost model that predicts a player's salary from their season
stats, for use as the "expected" salary in the over/underpaid valuation
(see ml/valuation.py).

Trains on every player_seasons row with both a salary and core stats
present (~10 seasons of history already in Postgres). `season` is included
as a feature so the model can absorb salary-cap inflation across years
instead of needing external cap data; this only holds for interpolation
within the trained season range, not for years far beyond it.

Run once, manually, from backend/ (as a module, so db/models/core resolve):
    python -m ml.train_valuation
"""

import logging

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, r2_score
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor

from db.database import SessionLocal
from models.salary import Player, PlayerSeason

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

ARTIFACT_PATH = "ml/artifacts/xgb_valuation.joblib"

# Stat columns the model trains on, plus `season` to capture cap inflation.
FEATURES = [
    "season",
    "points",
    "rebounds",
    "assists",
    "games_played",
    "games_started",
    "minutes_played",
    "per",
    "true_shooting_pct",
    "usage_pct",
    "offensive_win_shares",
    "defensive_win_shares",
    "win_shares",
    "win_shares_per_48",
    "offensive_bpm",
    "defensive_bpm",
    "box_plus_minus",
    "vorp",
]
TARGET = "salary"


def load_training_frame(db) -> pd.DataFrame:
    """Every (player, season, team) row with salary and stats populated."""
    rows = (
        db.query(PlayerSeason, Player.full_name)
        .join(Player, Player.id == PlayerSeason.player_id)
        .filter(PlayerSeason.salary.isnot(None))
        .filter(PlayerSeason.points.isnot(None))
        .filter(PlayerSeason.per.isnot(None))
        .all()
    )

    records = []
    for season_row, full_name in rows:
        record = {col: getattr(season_row, col) for col in FEATURES + [TARGET]}
        record["full_name"] = full_name
        records.append(record)

    df = pd.DataFrame.from_records(records)
    for col in FEATURES + [TARGET]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # A handful of advanced-stat columns (e.g. true_shooting_pct) have
    # occasional gaps even after the isnot(None) filters above (low-minute
    # seasons where bref leaves a cell blank); XGBoost handles NaN natively
    # via its missing-value split, so leave them rather than dropping rows.
    return df


def train(df: pd.DataFrame) -> XGBRegressor:
    X = df[FEATURES]
    y = np.log1p(df[TARGET])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = XGBRegressor(
        n_estimators=400,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_lambda=1.0,
        random_state=42,
    )
    model.fit(X_train, y_train)

    pred_test = np.expm1(model.predict(X_test))
    actual_test = np.expm1(y_test)

    mae = mean_absolute_error(actual_test, pred_test)
    mape = mean_absolute_percentage_error(actual_test, pred_test)
    r2 = r2_score(actual_test, pred_test)

    log.info(f"Test MAE:  ${mae:,.0f}")
    log.info(f"Test MAPE: {mape * 100:.1f}%")
    log.info(f"Test R^2:  {r2:.3f}")

    importances = sorted(
        zip(FEATURES, model.feature_importances_), key=lambda kv: kv[1], reverse=True
    )
    log.info("Feature importances:")
    for name, score in importances:
        log.info(f"  {name:<22} {score:.3f}")

    return model


def main():
    db = SessionLocal()
    try:
        df = load_training_frame(db)
    finally:
        db.close()

    log.info(f"Loaded {len(df)} training rows (seasons {int(df['season'].min())}-{int(df['season'].max())})")

    model = train(df)

    import pathlib
    pathlib.Path(ARTIFACT_PATH).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "features": FEATURES}, ARTIFACT_PATH)
    log.info(f"Saved model to {ARTIFACT_PATH}")


if __name__ == "__main__":
    main()
