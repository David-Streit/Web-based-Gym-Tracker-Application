from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from models.base import Base
from models.exercise import Exercise
from models.muscle_group import MuscleGroup
from models.personal_record import PersonalRecord
from models.session_muscle import SessionMuscle
from models.user import User
from models.weight_entry import WeightEntry, WeightGoal
from models.workout_session import WorkoutSession


@pytest.fixture(scope="function")
def in_memory_session():
    engine = create_engine("sqlite:///:memory:", echo=False, future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    with SessionLocal() as session:
        yield session


def test_create_user_and_related_records(in_memory_session):
    user = User(username="gymrat", password_hash="hashed_secret")
    session_entry = WorkoutSession(user=user, workout_date=date(2026, 5, 19), notes="Leg day")
    muscle = MuscleGroup(name="Legs", svg_key="legs")
    session_muscle = SessionMuscle(session=session_entry, muscle=muscle)
    exercise = Exercise(user=user, name="Squat")
    personal_record = PersonalRecord(
        user=user,
        exercise_name="Squat",
        weight_kg=140.0,
        recorded_date=date(2026, 5, 19),
    )
    weight_goal = WeightGoal(user=user, goal_kg=80.0)
    weight_entry = WeightEntry(user=user, entry_date=date(2026, 5, 18), weight_kg=82.5)

    in_memory_session.add_all([
        user,
        session_entry,
        muscle,
        session_muscle,
        exercise,
        personal_record,
        weight_goal,
        weight_entry,
    ])
    in_memory_session.commit()

    assert in_memory_session.query(User).count() == 1
    assert in_memory_session.query(WorkoutSession).count() == 1
    assert in_memory_session.query(MuscleGroup).count() == 1
    assert in_memory_session.query(SessionMuscle).count() == 1
    assert in_memory_session.query(Exercise).count() == 1
    assert in_memory_session.query(PersonalRecord).count() == 1
    assert in_memory_session.query(WeightGoal).count() == 1
    assert in_memory_session.query(WeightEntry).count() == 1

    persisted_user = in_memory_session.query(User).filter_by(username="gymrat").one()
    assert persisted_user.weight_goal.goal_kg == 80.0
    assert persisted_user.exercises[0].name == "Squat"
    assert persisted_user.workout_sessions[0].notes == "Leg day"


def test_unique_session_muscle_constraint_prevents_duplicate_relationships(in_memory_session):
    user = User(username="duplicate_test", password_hash="hashed_secret")
    workout_session = WorkoutSession(user=user, workout_date=date(2026, 5, 19))
    muscle = MuscleGroup(name="Back", svg_key="back")
    first_link = SessionMuscle(session=workout_session, muscle=muscle)

    in_memory_session.add_all([user, workout_session, muscle, first_link])
    in_memory_session.commit()

    duplicate_link = SessionMuscle(session=workout_session, muscle=muscle)
    in_memory_session.add(duplicate_link)

    with pytest.raises(IntegrityError):
        in_memory_session.commit()

    in_memory_session.rollback()
    assert in_memory_session.query(SessionMuscle).count() == 1


def test_transaction_rollback_removes_partial_changes(in_memory_session):
    first_user = User(username="rollback_test", password_hash="secret1")
    in_memory_session.add(first_user)
    in_memory_session.commit()

    with pytest.raises(IntegrityError):
        with in_memory_session.begin():
            duplicate_user = User(username="rollback_test", password_hash="secret2")
            in_memory_session.add(duplicate_user)
            in_memory_session.flush()

    in_memory_session.rollback()
    assert in_memory_session.query(User).filter_by(username="rollback_test").count() == 1
    assert in_memory_session.query(User).count() == 1
