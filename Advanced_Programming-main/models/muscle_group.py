from __future__ import annotations
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base
class MuscleGroup(Base):
    __tablename__ = "muscle_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    svg_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    session_muscles = relationship(
        "SessionMuscle",
        back_populates="muscle",
        cascade="all, delete-orphan",
    )