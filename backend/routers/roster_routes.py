from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from db.database import get_db
from models.roster import Roster, RosterPlayer
from models.salary import Player, PlayerSeason
from models.valuation import PlayerValuation
from schemas.rosters import RosterCreate, RosterOut, RosterPlayerAdd, RosterSummary

router = APIRouter(prefix="/rosters", tags=["rosters"])

MAX_ROSTER_SIZE = 15


def _player_rows(db: Session, roster_id: int):
    """
    One row per rostered player: their most recent season (team/salary) plus
    a matching valuation, if any. A player traded mid-season has multiple
    PlayerSeason rows for the same max season -- keep the stint with the
    most minutes, same convention as ml/valuation.py.
    """
    latest_season_subq = (
        db.query(
            PlayerSeason.player_id,
            func.max(PlayerSeason.season).label("season"),
        )
        .group_by(PlayerSeason.player_id)
        .subquery()
    )

    rows = (
        db.query(
            Player.id.label("player_id"),
            Player.full_name,
            Player.position,
            Player.headshot_url,
            PlayerSeason.team,
            PlayerSeason.salary,
            PlayerSeason.minutes_played,
            PlayerValuation.predicted_salary,
            PlayerValuation.verdict,
        )
        .join(RosterPlayer, RosterPlayer.player_id == Player.id)
        .outerjoin(
            latest_season_subq, latest_season_subq.c.player_id == Player.id
        )
        .outerjoin(
            PlayerSeason,
            (PlayerSeason.player_id == Player.id)
            & (PlayerSeason.season == latest_season_subq.c.season),
        )
        .outerjoin(
            PlayerValuation,
            (PlayerValuation.player_id == Player.id)
            & (PlayerValuation.season == PlayerSeason.season),
        )
        .filter(RosterPlayer.roster_id == roster_id)
        .all()
    )

    rows.sort(key=lambda r: r.minutes_played or 0, reverse=True)
    seen = set()
    deduped = []
    for row in rows:
        if row.player_id in seen:
            continue
        seen.add(row.player_id)
        deduped.append(row)

    return sorted(deduped, key=lambda r: r.full_name)


def _roster_out(db: Session, roster: Roster) -> RosterOut:
    rows = _player_rows(db, roster.id)
    total_salary = sum((r.salary for r in rows if r.salary is not None), Decimal(0))
    total_predicted_salary = sum(
        (r.predicted_salary for r in rows if r.predicted_salary is not None), Decimal(0)
    )

    return RosterOut(
        id=roster.id,
        name=roster.name,
        player_count=len(rows),
        total_salary=total_salary,
        total_predicted_salary=total_predicted_salary,
        players=rows,
    )


@router.post("", response_model=RosterOut, status_code=201)
def create_roster(payload: RosterCreate, db: Session = Depends(get_db)):
    player_ids = list(dict.fromkeys(payload.player_ids))

    if len(player_ids) > MAX_ROSTER_SIZE:
        raise HTTPException(
            status_code=400, detail=f"Roster cannot exceed {MAX_ROSTER_SIZE} players"
        )

    if player_ids:
        found_ids = {
            row.id
            for row in db.query(Player.id).filter(Player.id.in_(player_ids)).all()
        }
        missing = [pid for pid in player_ids if pid not in found_ids]
        if missing:
            raise HTTPException(
                status_code=404, detail=f"Player(s) not found: {missing}"
            )

    roster = Roster(name=payload.name)
    db.add(roster)
    db.flush()

    for player_id in player_ids:
        db.add(RosterPlayer(roster_id=roster.id, player_id=player_id))

    db.commit()
    db.refresh(roster)
    return _roster_out(db, roster)


@router.get("", response_model=list[RosterSummary])
def list_rosters(db: Session = Depends(get_db)):
    rosters = db.query(Roster).order_by(Roster.id).all()
    return [_roster_out(db, roster) for roster in rosters]


@router.get("/{roster_id}", response_model=RosterOut)
def get_roster(roster_id: int, db: Session = Depends(get_db)):
    roster = db.get(Roster, roster_id)
    if not roster:
        raise HTTPException(status_code=404, detail="Roster not found")
    return _roster_out(db, roster)


@router.delete("/{roster_id}", status_code=204)
def delete_roster(roster_id: int, db: Session = Depends(get_db)):
    roster = db.get(Roster, roster_id)
    if not roster:
        raise HTTPException(status_code=404, detail="Roster not found")
    db.delete(roster)
    db.commit()


@router.post("/{roster_id}/players", response_model=RosterOut, status_code=201)
def add_player(roster_id: int, payload: RosterPlayerAdd, db: Session = Depends(get_db)):
    roster = db.get(Roster, roster_id)
    if not roster:
        raise HTTPException(status_code=404, detail="Roster not found")

    player = db.get(Player, payload.player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    already_on = (
        db.query(RosterPlayer)
        .filter_by(roster_id=roster_id, player_id=payload.player_id)
        .first()
    )
    if already_on:
        raise HTTPException(status_code=400, detail="Player is already on this roster")

    current_count = (
        db.query(func.count(RosterPlayer.id))
        .filter(RosterPlayer.roster_id == roster_id)
        .scalar()
    )
    if current_count >= MAX_ROSTER_SIZE:
        raise HTTPException(
            status_code=400, detail=f"Roster is full (max {MAX_ROSTER_SIZE} players)"
        )

    db.add(RosterPlayer(roster_id=roster_id, player_id=payload.player_id))
    db.commit()
    return _roster_out(db, roster)


@router.delete("/{roster_id}/players/{player_id}", response_model=RosterOut)
def remove_player(roster_id: int, player_id: int, db: Session = Depends(get_db)):
    roster = db.get(Roster, roster_id)
    if not roster:
        raise HTTPException(status_code=404, detail="Roster not found")

    entry = (
        db.query(RosterPlayer)
        .filter_by(roster_id=roster_id, player_id=player_id)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Player is not on this roster")

    db.delete(entry)
    db.commit()
    return _roster_out(db, roster)
