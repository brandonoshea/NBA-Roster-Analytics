from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from db.database import get_db
from models.salary import Player
from models.salary import PlayerSeason
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
        )
        .join(Player, Player.id == PlayerSeason.player_id)
        .filter(PlayerSeason.season == latest_season)
        .order_by(PlayerSeason.points.desc().nullslast())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return players