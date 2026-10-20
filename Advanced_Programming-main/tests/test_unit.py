from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db import engine as db_engine
from db import session as db_session
from db.engine import init_db
from models.base import Base
from services.auth_service import AuthService
from services.weight_service import WeightService
from services.workout_service import WorkoutService


@pytest.fixture(autouse=True)
def in_memory_db(monkeypatch):
    engine = create_engine("sqlite:///:memory:", echo=False, future=True)
    Base.metadata.create_all(engine)

    monkeypatch.setattr(db_engine, "_ENGINE", engine)
    monkeypatch.setattr(
        db_session,
        "SessionLocal",
        sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True),
    )
    yield


def test_auth_service_registers_and_logs_in_user():
    auth_service = AuthService()
    user_id = auth_service.register("unit_user", "strongpass")

    assert isinstance(user_id, int)
    assert user_id > 0
    assert auth_service.login("unit_user", "strongpass") == user_id


def test_auth_service_rejects_duplicate_username():
    auth_service = AuthService()
    auth_service.register("duplicate_user", "password")

    with pytest.raises(ValueError, match="Username already exists"):
        auth_service.register("duplicate_user", "password2")


def test_auth_service_rejects_short_username():
    auth_service = AuthService()

    with pytest.raises(ValueError, match="Username must be at least 3 characters"):
        auth_service.register("ab", "password")


def test_workout_service_requires_at_least_one_muscle():
    init_db()
    workout_service = WorkoutService()

    with pytest.raises(ValueError, match="Select at least one muscle group"):
        workout_service.create_session(
            user_id=1,
            workout_date=date(2026, 5, 19),
            notes="No muscles",
            muscle_ids=[],
        )


def test_workout_service_rejects_future_dates():
    init_db()
    workout_service = WorkoutService()

    future_date = date.today().replace(year=date.today().year + 1)
    with pytest.raises(ValueError, match="Workout date cannot be in the future"):
        workout_service.create_session(
            user_id=1,
            workout_date=future_date,
            notes="Future workout",
            muscle_ids=[1],
        )


def test_weight_service_set_goal_and_get_goal():
    weight_service = WeightService()

    weight_service.set_goal(user_id=1, goal_kg=68.5)
    assert weight_service.get_goal(user_id=1) == 68.5
