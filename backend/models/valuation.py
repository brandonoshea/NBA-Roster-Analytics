from sqlalchemy import Column, Integer, Numeric, String, ForeignKey
from sqlalchemy.orm import relationship
from db.database import Base


class PlayerValuation(Base):
    __tablename__ = "player_valuations"

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id"), unique=True, nullable=False)
    season = Column(Integer, nullable=False)
    predicted_salary = Column(Numeric, nullable=False)
    actual_salary = Column(Numeric, nullable=True)
    verdict = Column(String, nullable=True)
    delta_pct = Column(Numeric, nullable=True)

    player = relationship("Player")