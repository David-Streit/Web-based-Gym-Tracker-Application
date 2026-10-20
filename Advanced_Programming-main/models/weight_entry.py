from __future__ import annotations
from datetime import date
from sqlalchemy import Date, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base

class WeightEntry(Base):
    __tablename__ = "weight_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    entry_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)

    user = relationship("User", back_populates="weight_entries")


class WeightGoal(Base):
    __tablename__ = "weight_goals"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    goal_kg: Mapped[float] = mapped_column(Float, nullable=False)

    user = relationship("User", back_populates="weight_goal")