from __future__ import annotations
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base
from models.personal_record import PersonalRecord
from models.weight_entry import WeightEntry
from models.workout_session import WorkoutSession
from models.exercise import Exercise

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # Admins can look up any user and view their entries (read-only)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")

    workout_sessions = relationship(
        "WorkoutSession",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    exercises = relationship(
        "Exercise",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    personal_records = relationship(
        "PersonalRecord",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    weight_entries = relationship(
        "WeightEntry",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    weight_goal = relationship(
        "WeightGoal",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )