from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from db.database import get_db
from models.salary import Player
from models.salary import PlayerSeason
from models.valuation import PlayerValuation
from schemas.players import PlayerListItem, PlayerSeasonOut

router = APIRouter(
    prefix="/players",
    tags=["players"]
)

@router.get("", response_model=list[PlayerSeasonOut])
def list_players(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    latest_season = db.query(func.max(PlayerSeason.season)).scalar()

    players = (
        db.query(
            Player.id.label("player_id"),
            Player.full_name,
            PlayerSeason.season,
            PlayerSeason.team,
            PlayerSeason.salary,
            PlayerSeason.points,
            PlayerSeason.rebounds,
            PlayerSeason.assists,
            PlayerSeason.games_played,
            PlayerSeason.games_started,
            PlayerSeason.minutes_played,
            PlayerSeason.per,
            PlayerSeason.true_shooting_pct,
            PlayerSeason.usage_pct,
            PlayerSeason.offensive_win_shares,
            PlayerSeason.defensive_win_shares,
            PlayerSeason.win_shares,
            PlayerSeason.win_shares_per_48,
            PlayerSeason.offensive_bpm,
            PlayerSeason.defensive_bpm,
            PlayerSeason.box_plus_minus,
            PlayerSeason.vorp,
            PlayerValuation.predicted_salary,
            PlayerValuation.verdict,
            PlayerValuation.delta_pct,
        )
        .join(Player, Player.id == PlayerSeason.player_id)
        .outerjoin(
            PlayerValuation,
            (PlayerValuation.player_id == Player.id)
            & (PlayerValuation.season == PlayerSeason.season),
        )
        .filter(PlayerSeason.season == latest_season)
        .order_by(PlayerSeason.points.desc().nullslast())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return players

@router.get("/{player_id}", response_model=list[PlayerListItem])
def get_player(player_id: int, db: Session = Depends(get_db)):
    seasons = (
        db.query(
            Player.id.label("player_id"),
            Player.full_name,
            Player.position,
            Player.headshot_url,
            PlayerSeason.season,
            PlayerSeason.team,
            PlayerSeason.salary,
            PlayerSeason.points,
            PlayerSeason.rebounds,
            PlayerSeason.assists,
            PlayerSeason.games_played,
            PlayerSeason.games_started,
            PlayerSeason.minutes_played,
            PlayerSeason.per,
            PlayerSeason.true_shooting_pct,
            PlayerSeason.usage_pct,
            PlayerSeason.offensive_win_shares,
            PlayerSeason.defensive_win_shares,
            PlayerSeason.win_shares,
            PlayerSeason.win_shares_per_48,
            PlayerSeason.offensive_bpm,
            PlayerSeason.defensive_bpm,
            PlayerSeason.box_plus_minus,
            PlayerSeason.vorp,
            PlayerValuation.predicted_salary,
            PlayerValuation.verdict,
            PlayerValuation.delta_pct,
        )
        .join(Player, Player.id == PlayerSeason.player_id)
        .outerjoin(
            PlayerValuation,
            (PlayerValuation.player_id == Player.id)
            & (PlayerValuation.season == PlayerSeason.season),
        )
        .filter(Player.id == player_id)
        .order_by(PlayerSeason.season.desc())
        .limit(10)
        .all()
    )

    if not seasons:
        raise HTTPException(status_code=404, detail="Player not found")

    return seasons
