from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from db.database import Base


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    full_name = Column(String, nullable=False)
    position = Column(String, nullable=True)
    nba_api_id = Column(String, unique=True, nullable=True)
    bref_id = Column(String, unique=True, nullable=True)
    headshot_url = Column(String, nullable=True)

    seasons = relationship("PlayerSeason", back_populates="player")


class PlayerSeason(Base):
    __tablename__ = "player_seasons"
    __table_args__ = (
        UniqueConstraint("player_id", "season", "team", name="uq_player_season_team"),
    )

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    season = Column(Integer, nullable=False)
    team = Column(String, nullable=False)
    salary = Column(Numeric, nullable=True)
    points = Column(Numeric, nullable=True)
    rebounds = Column(Numeric, nullable=True)
    assists = Column(Numeric, nullable=True)

    games_played = Column(Integer, nullable=True)
    games_started = Column(Integer, nullable=True)
    minutes_played = Column(Numeric, nullable=True)
    per = Column(Numeric, nullable=True)
    true_shooting_pct = Column(Numeric, nullable=True)
    usage_pct = Column(Numeric, nullable=True)
    offensive_win_shares = Column(Numeric, nullable=True)
    defensive_win_shares = Column(Numeric, nullable=True)
    win_shares = Column(Numeric, nullable=True)
    win_shares_per_48 = Column(Numeric, nullable=True)
    offensive_bpm = Column(Numeric, nullable=True)
    defensive_bpm = Column(Numeric, nullable=True)
    box_plus_minus = Column(Numeric, nullable=True)
    vorp = Column(Numeric, nullable=True)

    player = relationship("Player", back_populates="seasons")