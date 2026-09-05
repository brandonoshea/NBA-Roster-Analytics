from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal

class PlayerSeasonOut(BaseModel):
    player_id: int
    full_name: str
    season: int
    team: str
    salary: Optional[Decimal] = None
    points: Optional[Decimal] = None
    rebounds: Optional[Decimal] = None
    assists: Optional[Decimal] = None
    games_played: Optional[int] = None
    games_started: Optional[int] = None
    minutes_played: Optional[Decimal] = None
    per: Optional[Decimal] = None
    true_shooting_pct: Optional[Decimal] = None
    usage_pct: Optional[Decimal] = None
    offensive_win_shares: Optional[Decimal] = None
    defensive_win_shares: Optional[Decimal] = None
    win_shares: Optional[Decimal] = None
    win_shares_per_48: Optional[Decimal] = None
    offensive_bpm: Optional[Decimal] = None
    defensive_bpm: Optional[Decimal] = None
    box_plus_minus: Optional[Decimal] = None
    vorp: Optional[Decimal] = None

    class Config:
        from_attributes = True

class PlayerListItem(BaseModel):
    id: int
    full_name: str
    position: Optional[str] = None
    headshot_url: Optional[str] = None

    class Config:
        from_attributes = True