
from datetime import date

from pydantic import BaseModel, Field


class WorkoutCreate(BaseModel):
    workout_date: date
    notes: str | None = None

    muscle_ids: list[int] = Field(
        min_length=1,
        description="IDs of the trained muscle groups",
    )


class WorkoutUpdate(BaseModel):
    workout_date: date
    notes: str | None = None

    muscle_ids: list[int] = Field(
        min_length=1,
    )


class ExerciseCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
    )
