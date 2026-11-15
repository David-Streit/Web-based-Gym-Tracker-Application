"""API tests for the Milestone 3 user journey: log in, save a workout, get an error."""
from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from db import engine as db_engine
from db import session as db_session
from models.base import Base
from services.auth_service import AuthService


@pytest.fixture
def client():
    # one shared in-memory database for the test client's threads
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    db_engine._ENGINE = engine
    db_session.SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    from api.main import app
    with TestClient(app) as test_client:
        AuthService().register("lifter", "secret123")
        yield test_client


def login(client) -> dict:
    response = client.post("/api/auth/login", json={"username": "lifter", "password": "secret123"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['token']}"}


def test_login_with_wrong_password_returns_401(client):
    response = client.post("/api/auth/login", json={"username": "lifter", "password": "wrong"})
    assert response.status_code == 401


def test_create_workout_is_saved_and_listed(client):
    headers = login(client)
    body = {"workout_date": "2026-11-10", "notes": "Push day", "muscle_ids": [1, 2]}

    created = client.post("/api/workouts", json=body, headers=headers)
    assert created.status_code == 201
    workout_id = created.json()["id"]

    detail = client.get(f"/api/workouts/{workout_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["notes"] == "Push day"


def test_second_workout_on_same_day_is_rejected(client):
    headers = login(client)
    body = {"workout_date": "2026-11-10", "muscle_ids": [1]}

    assert client.post("/api/workouts", json=body, headers=headers).status_code == 201
    second = client.post("/api/workouts", json=body, headers=headers)
    assert second.status_code == 400
    assert "already" in second.json()["detail"]


def test_future_workout_date_is_rejected(client):
    headers = login(client)
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    response = client.post(
        "/api/workouts", json={"workout_date": tomorrow, "muscle_ids": [1]}, headers=headers
    )
    assert response.status_code == 400


def test_invalid_token_returns_401(client):
    response = client.get("/api/workouts", headers={"Authorization": "Bearer not-a-token"})
    assert response.status_code == 401


def test_exercises_endpoint_is_registered(client):
    headers = login(client)
    created = client.post("/api/exercises", json={"name": "Incline Press"}, headers=headers)
    assert created.status_code == 201
    listed = client.get("/api/exercises", headers=headers)
    assert listed.status_code == 200
    assert any(e["name"] == "Incline Press" for e in listed.json())
