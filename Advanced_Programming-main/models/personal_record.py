from __future__ import annotations
from datetime import date
from sqlalchemy import Date, ForeignKey, Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base

class PersonalRecord(Base):
    __tablename__ = "personal_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    exercise_name: Mapped[str] = mapped_column(String(100), nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    recorded_date: Mapped[date] = mapped_column(Date, nullable=False)

    user = relationship("User", back_populates="personal_records")