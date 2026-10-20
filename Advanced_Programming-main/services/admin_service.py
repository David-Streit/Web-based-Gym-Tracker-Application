from __future__ import annotations
from datetime import date
from typing import Any
from sqlalchemy import func
from db.session import get_session
from models.user import User
from models.workout_session import WorkoutSession
from services.workout_service import WorkoutService
from services.weight_service import WeightService


class AdminService:
    """
    Admins look up any normal user by name and manage that user's entries
    (workouts, personal records, weight entries, weight goal, exercises).
    Admins do not track workouts themselves.

    Every method checks that the caller is an admin, so the rule is enforced
    in the business logic and not only in the UI. The existing services are
    reused with the target user's id, so their validation and ownership
    checks (an entry must belong to that user) still apply.
    """

    def __init__(self, workout_service: WorkoutService, weight_service: WeightService):
        self.workout_service = workout_service
        self.weight_service = weight_service

    # access checks
    def _require_admin(self, admin_id: int | None) -> None:
        if admin_id is None:
            raise PermissionError("Not logged in.")
        with get_session() as session:
            user = session.get(User, admin_id)
            if user is None or not user.is_admin:
                raise PermissionError("Admin rights required.")

    def _require_normal_user(self, user_id: int) -> None:
        with get_session() as session:
            user = session.get(User, user_id)
            if user is None or user.is_admin:
                raise ValueError("User not found.")

    # search / read
    def search_users(self, admin_id: int, query: str = "") -> list[dict[str, Any]]:
        """Normal users whose name contains `query` (case-insensitive), with workout counts."""
        self._require_admin(admin_id)
        query = (query or "").strip()

        with get_session() as session:
            q = (
                session.query(User, func.count(WorkoutSession.id))
                .outerjoin(WorkoutSession, WorkoutSession.user_id == User.id)
                .filter(User.is_admin.is_(False))
                .group_by(User.id)
                .order_by(User.username.asc())
            )
            if query:
                q = q.filter(User.username.ilike(f"%{query}%"))

            return [
                {"id": user.id, "username": user.username, "workout_count": count}
                for user, count in q.all()
            ]

    def get_user_entries(self, admin_id: int, username: str) -> dict[str, Any]:
        """All entries of one normal user, looked up by exact username."""
        self._require_admin(admin_id)
        username = (username or "").strip()
        if not username:
            raise ValueError("Please enter a username.")

        with get_session() as session:
            user = (
                session.query(User)
                .filter(User.username == username, User.is_admin.is_(False))
                .first()
            )
            if user is None:
                raise ValueError(f"User '{username}' not found.")
            user_id, name = user.id, user.username

        muscle_ids_by_name = {m["name"]: m["id"] for m in self.workout_service.list_muscles()}
        workouts = self.workout_service.list_sessions(user_id=user_id, limit=10_000)
        for w in workouts:
            w["muscle_ids"] = [muscle_ids_by_name[n] for n in w["muscle_names"] if n in muscle_ids_by_name]

        return {
            "user": {"id": user_id, "username": name},
            "workouts": workouts,
            "exercises": self.workout_service.list_exercises(user_id),
            "personal_records": self.workout_service.get_all_prs_by_exercise(user_id),
            "weight_entries": self.weight_service.list_entries(user_id),
            "weight_goal": self.weight_service.get_goal(user_id),
        }

    def list_muscles(self, admin_id: int) -> list[dict[str, Any]]:
        self._require_admin(admin_id)
        return self.workout_service.list_muscles()

    # workouts
    def update_workout(
        self,
        admin_id: int,
        user_id: int,
        session_id: int,
        workout_date: date,
        notes: str | None,
        muscle_ids: list[int],
    ) -> None:
        self._require_admin(admin_id)
        self._require_normal_user(user_id)
        if workout_date > date.today():
            raise ValueError("Workout date cannot be in the future.")
        # same rule as when creating: one workout per user and day
        for other in self.workout_service.list_sessions_in_range(user_id, workout_date, workout_date):
            if other["id"] != session_id:
                raise ValueError("This user already has a workout on that day.")
        self.workout_service.update_session(session_id, user_id, workout_date, notes, muscle_ids)

    def delete_workout(self, admin_id: int, user_id: int, session_id: int) -> None:
        self._require_admin(admin_id)
        self._require_normal_user(user_id)
        self.workout_service.delete_session(session_id, user_id)

    # personal records
    def update_pr(self, admin_id: int, user_id: int, pr_id: int, weight_kg: float, recorded_date: date) -> None:
        self._require_admin(admin_id)
        self._require_normal_user(user_id)
        self.workout_service.update_pr(pr_id, user_id, weight_kg, recorded_date)

    def delete_pr(self, admin_id: int, user_id: int, pr_id: int) -> None:
        self._require_admin(admin_id)
        self._require_normal_user(user_id)
        self.workout_service.delete_pr(pr_id, user_id)

    # body weight
    def update_weight_entry(
        self, admin_id: int, user_id: int, entry_id: int, entry_date: date, weight_kg: float
    ) -> None:
        self._require_admin(admin_id)
        self._require_normal_user(user_id)
        self.weight_service.update_entry(entry_id, user_id, entry_date, weight_kg)

    def delete_weight_entry(self, admin_id: int, user_id: int, entry_id: int) -> None:
        self._require_admin(admin_id)
        self._require_normal_user(user_id)
        self.weight_service.delete_entry(entry_id, user_id)

    def set_weight_goal(self, admin_id: int, user_id: int, goal_kg: float) -> None:
        self._require_admin(admin_id)
        self._require_normal_user(user_id)
        self.weight_service.set_goal(user_id, goal_kg)

    # exercises
    def create_exercise(self, admin_id: int, user_id: int, name: str) -> int:
        self._require_admin(admin_id)
        self._require_normal_user(user_id)
        return self.workout_service.create_exercise(user_id, name)

    def delete_exercise(self, admin_id: int, user_id: int, exercise_id: int) -> None:
        self._require_admin(admin_id)
        self._require_normal_user(user_id)
        self.workout_service.delete_exercise(exercise_id, user_id)
