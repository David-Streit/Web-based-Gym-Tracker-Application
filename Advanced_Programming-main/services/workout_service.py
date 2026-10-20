from __future__ import annotations
from datetime import date
from typing import Any
from db.session import get_session
from models.muscle_group import MuscleGroup
from models.session_muscle import SessionMuscle
from models.workout_session import WorkoutSession
from models.exercise import Exercise

class WorkoutService:
    """
    MVP: Workouts = date + notes + selected muscle groups.
    """

    # muscles
    def list_muscles(self) -> list[dict[str, Any]]:
        with get_session() as session:
            muscles = session.query(MuscleGroup).order_by(MuscleGroup.id.asc()).all()
            return [{"id": m.id, "name": m.name, "svg_key": m.svg_key} for m in muscles]

    #Sessions
    def create_session(
        self,
        user_id: int,
        workout_date: date,
        notes: str | None,
        muscle_ids: list[int],
    ) -> int:
        if not muscle_ids:
            raise ValueError("Select at least one muscle group.")
#Date Validation
        if workout_date > date.today():
            raise ValueError("Workout date cannot be in the future.")

        with get_session() as session:
            existing_session = session.query(WorkoutSession).filter(
                WorkoutSession.user_id == user_id,
                WorkoutSession.workout_date == workout_date
            ).first()
            
            if existing_session:
                raise ValueError("You already have a tracked training for this day.")

            ws = WorkoutSession(user_id=user_id, workout_date=workout_date, notes=notes)
            session.add(ws)
            session.commit()
            session.refresh(ws)

            # Create join rows (session <-> muscle)
            for mid in set(muscle_ids):
                link = SessionMuscle(workout_session_id=ws.id, muscle_group_id=mid)
                session.add(link)

            session.commit()
            return ws.id
        
    def list_sessions(self, user_id: int, limit: int = 20) -> list[dict[str, Any]]:
        """
        Returns list of dicts:
        {id, date, notes, muscle_names[]}
        """
        with get_session() as session:
            sessions = (
                session.query(WorkoutSession)
                .filter(WorkoutSession.user_id == user_id)
                .order_by(WorkoutSession.workout_date.desc(), WorkoutSession.id.desc())
                .limit(limit)
                .all()
            )

            result: list[dict[str, Any]] = []
            for ws in sessions:
                muscle_names = (
                    session.query(MuscleGroup.name)
                    .join(SessionMuscle, SessionMuscle.muscle_group_id == MuscleGroup.id)
                    .filter(SessionMuscle.workout_session_id == ws.id)
                    .order_by(MuscleGroup.id.asc())
                    .all()
                )
                # muscle_names is list of tuples [(name,), ...]
                names = [mn[0] for mn in muscle_names]

                result.append(
                    {
                        "id": ws.id,
                        "date": ws.workout_date,
                        "notes": ws.notes,
                        "muscle_names": names,
                    }
                )

            return result

    def delete_session(self, session_id: int, user_id: int) -> None:
        with get_session() as session:
            ws = (
                session.query(WorkoutSession)
                .filter(WorkoutSession.id == session_id, WorkoutSession.user_id == user_id)
                .first()
            )
            if ws is None:
                raise ValueError("Workout not found (or not yours).")

            session.delete(ws)
            session.commit()

    def list_sessions_in_range(
        self,
        user_id: int,
        start_date: date,
        end_date: date,
    ) -> list[dict[str, Any]]:
        """
        Used by MuscleMapService. Inclusive range: start_date..end_date
        """
        with get_session() as session:
            sessions = (
                session.query(WorkoutSession)
                .filter(
                    WorkoutSession.user_id == user_id,
                    WorkoutSession.workout_date >= start_date,
                    WorkoutSession.workout_date <= end_date,
                )
                .order_by(WorkoutSession.workout_date.asc(), WorkoutSession.id.asc())
                .all()
            )

            result: list[dict[str, Any]] = []
            for ws in sessions:
                muscle_names = (
                    session.query(MuscleGroup.name)
                    .join(SessionMuscle, SessionMuscle.muscle_group_id == MuscleGroup.id)
                    .filter(SessionMuscle.workout_session_id == ws.id)
                    .order_by(MuscleGroup.id.asc())
                    .all()
                )
                names = [mn[0] for mn in muscle_names]

                result.append(
                    {
                        "id": ws.id,
                        "date": ws.workout_date,
                        "notes": ws.notes,
                        "muscle_names": names,
                    }
                )
            return result
        
    def get_session_by_id(self, session_id: int, user_id: int) -> dict:
        with get_session() as session:
            ws = (
                session.query(WorkoutSession)
                .filter(
                    WorkoutSession.id == session_id,
                    WorkoutSession.user_id == user_id,
                )
                .first()
            )

            if ws is None:
                raise ValueError("Workout not found.")

            muscle_links = (
                session.query(SessionMuscle.muscle_group_id)
                .filter(SessionMuscle.workout_session_id == ws.id)
                .all()
            )

            muscle_ids = [m[0] for m in muscle_links]

            return {
                "id": ws.id,
                "date": ws.workout_date,
                "notes": ws.notes,
                "muscle_ids": muscle_ids,
            }


    def update_session(
        self,
        session_id: int,
        user_id: int,
        workout_date: date,
        notes: str | None,
        muscle_ids: list[int],
    ) -> None:
        if not muscle_ids:
            raise ValueError("Select at least one muscle group.")

        with get_session() as session:
            ws = (
                session.query(WorkoutSession)
                .filter(
                    WorkoutSession.id == session_id,
                    WorkoutSession.user_id == user_id,
                )
                .first()
            )

            if ws is None:
                raise ValueError("Workout not found.")

            ws.workout_date = workout_date
            ws.notes = notes

            session.query(SessionMuscle).filter(
                SessionMuscle.workout_session_id == ws.id
            ).delete()

            for mid in set(muscle_ids):
                session.add(SessionMuscle(
                    workout_session_id=ws.id,
                    muscle_group_id=mid,
                ))

            session.commit()

    def get_last_workout_date(self, user_id: int) -> date | None:
        """Retrieves only the date of the most recent workout session."""
        with get_session() as session:
            ws = (
                session.query(WorkoutSession)
                .filter(WorkoutSession.user_id == user_id)
                .order_by(WorkoutSession.workout_date.desc(), WorkoutSession.id.desc())
                .first()
            )
            return ws.workout_date if ws else None
    
    #Custom Exercises
    def list_exercises(self, user_id: int) -> list[dict[str, Any]]:
        with get_session() as session:
            exercises = (
                session.query(Exercise)
                .filter(Exercise.user_id == user_id)
                .order_by(Exercise.id.asc())
                .all()
            )
            return [{"id": e.id, "name": e.name} for e in exercises]

    def create_exercise(self, user_id: int, name: str) -> int:
        if not name or not name.strip():
            raise ValueError("Exercise name cannot be empty.")
        
        with get_session() as session:
            # Check if exercise already exists for this user
            existing = (
                session.query(Exercise)
                .filter(Exercise.user_id == user_id, Exercise.name == name.strip())
                .first()
            )
            if existing:
                raise ValueError(f"Exercise '{name}' already exists.")
            
            exercise = Exercise(user_id=user_id, name=name.strip())
            session.add(exercise)
            session.commit()
            session.refresh(exercise)
            return exercise.id

    def delete_exercise(self, exercise_id: int, user_id: int) -> None:
        with get_session() as session:
            exercise = (
                session.query(Exercise)
                .filter(Exercise.id == exercise_id, Exercise.user_id == user_id)
                .first()
            )
            if exercise is None:
                raise ValueError("Exercise not found.")
            
            session.delete(exercise)
            session.commit()
            
#Personal Records
    def save_pr(self, user_id: int, exercise_name: str, weight_kg: float, recorded_date: date) -> None:
        if weight_kg <= 0:
            raise ValueError("Weight must be greater than zero.")
        if recorded_date > date.today():
            raise ValueError("PR date cannot be in the future.")
        from models.personal_record import PersonalRecord
        with get_session() as session:
            pr = PersonalRecord(
                user_id=user_id,
                exercise_name=exercise_name,
                weight_kg=weight_kg,
                recorded_date=recorded_date,
            )
            session.add(pr)
            session.commit()

    def get_best_prs(self, user_id: int) -> list[dict]:
        from models.personal_record import PersonalRecord
        with get_session() as session:
            records = (
                session.query(PersonalRecord)
                .filter(PersonalRecord.user_id == user_id)
                .order_by(
                    PersonalRecord.exercise_name.asc(),
                    PersonalRecord.weight_kg.desc(),
                    PersonalRecord.recorded_date.desc(),
                )
                .all()
            )
            seen = {}
            for r in records:
                if r.exercise_name not in seen:
                    seen[r.exercise_name] = {
                        "id": r.id,
                        "exercise": r.exercise_name,
                        "weight_kg": r.weight_kg,
                        "date": r.recorded_date,
                    }
            return list(seen.values())
        
    def get_all_prs_by_exercise(self, user_id: int) -> dict[str, list[dict]]:
        from models.personal_record import PersonalRecord
        with get_session() as session:
            records = (
                session.query(PersonalRecord)
                .filter(PersonalRecord.user_id == user_id)
                .order_by(
                    PersonalRecord.exercise_name.asc(),
                    PersonalRecord.recorded_date.asc(),
                )
                .all()
            )
            grouped: dict[str, list[dict]] = {}
            for r in records:
                grouped.setdefault(r.exercise_name, []).append({
                    "id": r.id,
                    "weight_kg": r.weight_kg,
                    "date": r.recorded_date,
                })
            return grouped

    def get_pr_by_id(self, pr_id: int, user_id: int) -> dict:
        from models.personal_record import PersonalRecord
        with get_session() as session:
            pr = (
                session.query(PersonalRecord)
                .filter(
                    PersonalRecord.id == pr_id,
                    PersonalRecord.user_id == user_id,
                )
                .first()
            )
            if pr is None:
                raise ValueError("Personal record not found.")
            return {
                "id": pr.id,
                "exercise": pr.exercise_name,
                "weight_kg": pr.weight_kg,
                "date": pr.recorded_date,
            }

    def update_pr(self, pr_id: int, user_id: int, weight_kg: float, recorded_date: date) -> None:
        if weight_kg <= 0:
            raise ValueError("Weight must be greater than zero.")
        if recorded_date > date.today():
            raise ValueError("PR date cannot be in the future.")
        with get_session() as session:
            from models.personal_record import PersonalRecord
            pr = (
                session.query(PersonalRecord)
                .filter(
                    PersonalRecord.id == pr_id,
                    PersonalRecord.user_id == user_id,
                )
                .first()
            )
            if pr is None:
                raise ValueError("Personal record not found.")
            pr.weight_kg = weight_kg
            pr.recorded_date = recorded_date
            session.commit()

    def delete_pr(self, pr_id: int, user_id: int) -> None:
        with get_session() as session:
            from models.personal_record import PersonalRecord
            pr = (
                session.query(PersonalRecord)
                .filter(
                    PersonalRecord.id == pr_id,
                    PersonalRecord.user_id == user_id,
                )
                .first()
            )
            if pr is None:
                raise ValueError("Personal record not found.")
            session.delete(pr)
            session.commit()
    
