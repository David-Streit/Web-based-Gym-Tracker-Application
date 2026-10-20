from __future__ import annotations
from datetime import date
from typing import Any
from utils.dates import week_range

class MuscleMapService:
    def __init__(self, workout_service) -> None:
        self.workout_service = workout_service

    def week_summary(self, user_id: int, day_in_week: date) -> dict[str, Any]:
        # determine the current week range for the requested date
        week_start, week_end = week_range(day_in_week)

        # load all workouts for the user during this week
        sessions = self.workout_service.list_sessions_in_range(
            user_id=user_id,
            start_date=week_start,
            end_date=week_end,
        )

        counts: dict[str, int] = {}
        for s in sessions:
            for m in s["muscle_names"]:
                # count each muscle occurrence across the week's sessions
                counts[m] = counts.get(m, 0) + 1

        def intensity_from_count(c: int) -> int:
            # convert muscle hit counts into a simple intensity scale
            if c <= 0:
                return 0
            if c == 1:
                return 1
            if c == 2:
                return 2
            return 3

        muscles = [
            {"name": name, "count": cnt, "intensity": intensity_from_count(cnt)}
            for name, cnt in sorted(counts.items(), key=lambda x: x[0].lower())
        ]

        return {
            "week_start": week_start,
            "week_end": week_end,
            "muscles": muscles,
        }