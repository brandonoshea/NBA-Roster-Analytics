from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal

class PlayerSeasonOut(BaseModel):
    season: int
    team: str
    salary: Optional[Decimal] = None
    points: Optional[Decimal] = None
    rebounds: Optional[Decimal] = None
    assists: Optional[Decimal] = None
    games_played: Optional[int] = None
    minutes_played: Optional[Decimal] = None
    per: Optional[Decimal] = None
    true_shooting_pct: Optional[Decimal] = None
    win_shares: Optional[Decimal] = None
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