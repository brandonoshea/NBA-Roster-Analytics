from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class RosterCreate(BaseModel):
    name: str
    player_ids: List[int] = []


class RosterPlayerAdd(BaseModel):
    player_id: int


class RosterPlayerOut(BaseModel):
    player_id: int
    full_name: str
    position: Optional[str] = None
    headshot_url: Optional[str] = None
    team: Optional[str] = None
    salary: Optional[Decimal] = None
    predicted_salary: Optional[Decimal] = None
    verdict: Optional[str] = None

    class Config:
        from_attributes = True


class RosterSummary(BaseModel):
    id: int
    name: str
    player_count: int
    total_salary: Decimal
    total_predicted_salary: Decimal

    class Config:
        from_attributes = True


class RosterOut(RosterSummary):
    players: List[RosterPlayerOut]
