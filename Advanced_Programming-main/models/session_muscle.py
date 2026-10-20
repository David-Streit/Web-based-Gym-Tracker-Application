from __future__ import annotations
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base
class SessionMuscle(Base):
    """
    Join table: WorkoutSession <-> MuscleGroup (many-to-many)
    """
    __tablename__ = "session_muscles"
    __table_args__ = (
        UniqueConstraint("workout_session_id", "muscle_group_id", name="uq_session_muscle"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    workout_session_id: Mapped[int] = mapped_column(
        ForeignKey("workout_sessions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    muscle_group_id: Mapped[int] = mapped_column(
        ForeignKey("muscle_groups.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    session = relationship("WorkoutSession", back_populates="session_muscles")
    muscle = relationship("MuscleGroup", back_populates="session_muscles")