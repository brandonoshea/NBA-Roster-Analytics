from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from db.database import Base


class Roster(Base):
    __tablename__ = "rosters"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    players = relationship(
        "RosterPlayer", back_populates="roster", cascade="all, delete-orphan"
    )


class RosterPlayer(Base):
    __tablename__ = "roster_players"
    __table_args__ = (
        UniqueConstraint("roster_id", "player_id", name="uq_roster_player"),
    )

    id = Column(Integer, primary_key=True)
    roster_id = Column(Integer, ForeignKey("rosters.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)

    roster = relationship("Roster", back_populates="players")
    player = relationship("Player")
