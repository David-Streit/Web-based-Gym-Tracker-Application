from __future__ import annotations
from datetime import date
from typing import Any
from db.session import get_session
from models.weight_entry import WeightEntry, WeightGoal

class WeightService:

    def add_entry(self, user_id: int, entry_date: date, weight_kg: float) -> None:
        # add or update a user's weight log for a specific date
        if weight_kg <= 0:
            raise ValueError("Weight must be greater than zero.")
        if entry_date > date.today():
            raise ValueError("Entry date cannot be in the future.")
        with get_session() as session:
            # find an existing entry for the same user and date
            existing = (
                session.query(WeightEntry)
                .filter(WeightEntry.user_id == user_id, WeightEntry.entry_date == entry_date)
                .first()
            )
            if existing:
                existing.weight_kg = weight_kg
            else:
                session.add(WeightEntry(user_id=user_id, entry_date=entry_date, weight_kg=weight_kg))
            session.commit()

    def list_entries(self, user_id: int) -> list[dict[str, Any]]:
        # retrieve all weight records for the user, newest first
        with get_session() as session:
            entries = (
                session.query(WeightEntry)
                .filter(WeightEntry.user_id == user_id)
                .order_by(WeightEntry.entry_date.desc())
                .all()
            )
            return [{"id": e.id, "date": e.entry_date, "weight_kg": e.weight_kg} for e in entries]

    def update_entry(self, entry_id: int, user_id: int, entry_date: date, weight_kg: float) -> None:
        # change date and/or weight of an existing entry belonging to the user
        if weight_kg <= 0:
            raise ValueError("Weight must be greater than zero.")
        if entry_date > date.today():
            raise ValueError("Entry date cannot be in the future.")
        with get_session() as session:
            entry = (
                session.query(WeightEntry)
                .filter(WeightEntry.id == entry_id, WeightEntry.user_id == user_id)
                .first()
            )
            if entry is None:
                raise ValueError("Entry not found.")
            clash = (
                session.query(WeightEntry)
                .filter(
                    WeightEntry.user_id == user_id,
                    WeightEntry.entry_date == entry_date,
                    WeightEntry.id != entry_id,
                )
                .first()
            )
            if clash:
                raise ValueError("There is already a weight entry for this date.")
            entry.entry_date = entry_date
            entry.weight_kg = weight_kg
            session.commit()

    def delete_entry(self, entry_id: int, user_id: int) -> None:
        # remove a specific weight log belonging to the user
        with get_session() as session:
            entry = (
                session.query(WeightEntry)
                .filter(WeightEntry.id == entry_id, WeightEntry.user_id == user_id)
                .first()
            )
            if entry is None:
                raise ValueError("Entry not found.")
            session.delete(entry)
            session.commit()

    def set_goal(self, user_id: int, goal_kg: float) -> None:
        # record or update the user's target weight goal
        if goal_kg <= 0:
            raise ValueError("Goal weight must be greater than zero.")
        with get_session() as session:
            goal = (
                session.query(WeightGoal)
                .filter(WeightGoal.user_id == user_id)
                .first()
            )
            if goal:
                goal.goal_kg = goal_kg
            else:
                session.add(WeightGoal(user_id=user_id, goal_kg=goal_kg))
            session.commit()

    def get_goal(self, user_id: int) -> float | None:
        # fetch the current saved weight goal for the user
        with get_session() as session:
            goal = (
                session.query(WeightGoal)
                .filter(WeightGoal.user_id == user_id)
                .first()
            )
            return goal.goal_kg if goal else None