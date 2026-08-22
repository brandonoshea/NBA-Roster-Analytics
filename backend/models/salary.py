from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy import func
#sql alchemy writes sql for simple python operations.
from db.database import Base
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship

from db import Base


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    full_name = Column(String, nullable=False)
    position = Column(String, nullable=True)

    seasons = relationship("PlayerSeason", back_populates="player")


class PlayerSeason(Base):
    __tablename__ = "player_seasons"

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    season = Column(Integer, nullable=False)
    team = Column(String, nullable=False)
    salary = Column(Numeric, nullable=True)
    points = Column(Numeric, nullable=True)
    rebounds = Column(Numeric, nullable=True)
    assists = Column(Numeric, nullable=True)

    player = relationship("Player", back_populates="seasons")