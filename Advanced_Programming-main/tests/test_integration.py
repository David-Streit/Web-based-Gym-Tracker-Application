from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from db import engine as db_engine
from db import session as db_session
from db.engine import init_db
from models.base import Base
from models.session_muscle import SessionMuscle
from models.user import User
from services.auth_service import AuthService
from services.weight_service import WeightService
from services.workout_service import WorkoutService


@pytest.fixture(autouse=True)
def in_memory_db(monkeypatch):
    engine = create_engine("sqlite:///:memory:", echo=False, future=True)
    Base.metadata.create_all(engine)
    db_engine._ENGINE = engine
    db_session.SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    yield


def test_register_user_create_workout_and_goal():
    init_db()

    auth_service = AuthService()
    workout_service = WorkoutService()
    weight_service = WeightService()

    user_id = auth_service.register("integration_user", "password")
    assert user_id > 0

    muscles = workout_service.list_muscles()
    assert muscles
    muscle_id = muscles[0]["id"]

    session_id = workout_service.create_session(
        user_id=user_id,
        workout_date=date(2026, 5, 19),
        notes="Integration test workout",
        muscle_ids=[muscle_id],
    )
    assert session_id > 0

    sessions = workout_service.list_sessions(user_id)
    assert len(sessions) == 1
    assert sessions[0]["notes"] == "Integration test workout"
    assert sessions[0]["muscle_names"] == [muscles[0]["name"]]

    weight_service.set_goal(user_id, 75.0)
    assert weight_service.get_goal(user_id) == 75.0


def test_duplicate_muscle_ids_do_not_create_duplicate_session_muscle_rows():
    init_db()

    auth_service = AuthService()
    workout_service = WorkoutService()

    user_id = auth_service.register("muscle_duplicate", "password")
    muscles = workout_service.list_muscles()
    muscle_id = muscles[0]["id"]

    session_id = workout_service.create_session(
        user_id=user_id,
        workout_date=date(2026, 5, 19),
        notes="Duplicate muscle ids",
        muscle_ids=[muscle_id, muscle_id],
    )

    with db_session.get_session() as session:
        links = session.query(SessionMuscle).filter(SessionMuscle.workout_session_id == session_id).all()
        assert len(links) == 1

    retrieved = workout_service.get_session_by_id(session_id, user_id)
    assert retrieved["muscle_ids"] == [muscle_id]


def test_register_duplicate_username_does_not_create_second_user():
    init_db()

    auth_service = AuthService()
    user_id = auth_service.register("rollback_user", "password")
    assert user_id > 0

    with pytest.raises(ValueError, match="Username already exists"):
        auth_service.register("rollback_user", "newpass")

    with db_session.get_session() as session:
        users = session.query(User).filter(User.username == "rollback_user").all()
        assert len(users) == 1
