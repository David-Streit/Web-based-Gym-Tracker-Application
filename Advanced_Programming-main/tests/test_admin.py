from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from db import engine as db_engine
from db import session as db_session
from db.engine import DEFAULT_ADMIN_PASSWORD, DEFAULT_ADMIN_USERNAME, init_db
from models.base import Base
from services.admin_service import AdminService
from services.auth_service import AuthService
from services.weight_service import WeightService
from services.workout_service import WorkoutService


@pytest.fixture(autouse=True)
def in_memory_db(monkeypatch):
    monkeypatch.delenv("ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    engine = create_engine("sqlite:///:memory:", echo=False, future=True)
    Base.metadata.create_all(engine)
    db_engine._ENGINE = engine
    db_session.SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    yield


@pytest.fixture
def services():
    init_db()
    workout = WorkoutService()
    weight = WeightService()
    return AuthService(), workout, weight, AdminService(workout, weight)


def test_init_db_seeds_admin_that_can_log_in(services):
    auth, *_ = services
    admin_id = auth.login(DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD)
    assert auth.is_admin(admin_id)
    assert auth.get_user_by_id(admin_id)["is_admin"] is True


def test_init_db_does_not_create_second_admin(services):
    init_db()
    from db.session import get_session
    from models.user import User
    with get_session() as session:
        assert session.query(User).filter(User.is_admin.is_(True)).count() == 1


def test_admins_are_not_listed_or_editable(services):
    auth, _, _, admin = services
    admin_id = auth.login(DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD)
    auth.register("lifter", "secret")
    assert [u["username"] for u in admin.search_users(admin_id)] == ["lifter"]
    with pytest.raises(ValueError):
        admin.get_user_entries(admin_id, DEFAULT_ADMIN_USERNAME)
    with pytest.raises(ValueError):
        admin.set_weight_goal(admin_id, admin_id, 80)


def test_registered_users_are_not_admins(services):
    auth, *_ = services
    user_id = auth.register("lifter", "secret")
    assert auth.is_admin(user_id) is False


def test_admin_sees_entries_of_requested_user(services):
    auth, workout, weight, admin = services
    admin_id = auth.login(DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD)

    user_id = auth.register("anna", "secret")
    muscle_id = workout.list_muscles()[0]["id"]
    workout.create_session(user_id, date(2026, 5, 1), "Push day", [muscle_id])
    workout.create_exercise(user_id, "Bench Press")
    workout.save_pr(user_id, "Bench Press", 80.0, date(2026, 5, 1))
    weight.add_entry(user_id, date(2026, 5, 1), 70.5)
    weight.set_goal(user_id, 68.0)

    other_id = auth.register("bob", "secret")
    workout.create_session(other_id, date(2026, 5, 2), "Bob only", [muscle_id])

    data = admin.get_user_entries(admin_id, "anna")

    assert data["user"]["username"] == "anna"
    assert [w["notes"] for w in data["workouts"]] == ["Push day"]
    assert data["exercises"][0]["name"] == "Bench Press"
    assert data["personal_records"]["Bench Press"][0]["weight_kg"] == 80.0
    assert data["weight_entries"][0]["weight_kg"] == 70.5
    assert data["weight_goal"] == 68.0


def test_unknown_username_raises(services):
    auth, _, _, admin = services
    admin_id = auth.login(DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD)
    with pytest.raises(ValueError):
        admin.get_user_entries(admin_id, "does_not_exist")


def test_normal_user_cannot_use_admin_functions(services):
    auth, _, _, admin = services
    user_id = auth.register("curious", "secret")
    auth.register("victim", "secret")

    with pytest.raises(PermissionError):
        admin.get_user_entries(user_id, "victim")
    with pytest.raises(PermissionError):
        admin.search_users(user_id)
    with pytest.raises(PermissionError):
        admin.search_users(None)


def test_search_users_filters_case_insensitive(services):
    auth, _, _, admin = services
    admin_id = auth.login(DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD)
    auth.register("MaxMuster", "secret")
    auth.register("maxine", "secret")
    auth.register("tim", "secret")

    names = [u["username"] for u in admin.search_users(admin_id, "max")]
    assert names == ["MaxMuster", "maxine"]


def test_is_admin_column_added_to_old_database():
    engine = create_engine("sqlite:///:memory:", echo=False, future=True)
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE users (id INTEGER PRIMARY KEY, username VARCHAR(50) UNIQUE NOT NULL, "
            "password_hash VARCHAR(255) NOT NULL)"
        ))
        conn.execute(text("INSERT INTO users (username, password_hash) VALUES ('old_user', 'x')"))
    db_engine._ENGINE = engine
    db_session.SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    init_db()

    columns = {c["name"] for c in inspect(engine).get_columns("users")}
    assert "is_admin" in columns
    with engine.connect() as conn:
        assert conn.execute(text("SELECT is_admin FROM users WHERE username='old_user'")).scalar() == 0


@pytest.fixture
def anna(services):
    """Admin id, anna's id and her entries."""
    auth, workout, weight, admin = services
    admin_id = auth.login(DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD)
    uid = auth.register("anna", "secret")
    muscles = [m["id"] for m in workout.list_muscles()]
    workout.create_session(uid, date(2026, 5, 1), "Push day", [muscles[1]])
    workout.create_session(uid, date(2026, 5, 3), "Legs", [muscles[0]])
    workout.create_exercise(uid, "Bench Press")
    workout.save_pr(uid, "Bench Press", 80.0, date(2026, 5, 1))
    weight.add_entry(uid, date(2026, 5, 1), 70.5)
    weight.add_entry(uid, date(2026, 5, 2), 70.0)
    return admin_id, uid, admin.get_user_entries(admin_id, "anna"), muscles


def test_admin_edits_workout(services, anna):
    *_, admin = services
    admin_id, uid, data, muscles = anna
    push = next(w for w in data["workouts"] if w["notes"] == "Push day")
    admin.update_workout(admin_id, uid, push["id"], date(2026, 5, 2), "Corrected", [muscles[2], muscles[3]])

    updated = next(w for w in admin.get_user_entries(admin_id, "anna")["workouts"] if w["id"] == push["id"])
    assert updated["date"] == date(2026, 5, 2)
    assert updated["notes"] == "Corrected"
    assert updated["muscle_ids"] == [muscles[2], muscles[3]]


def test_admin_workout_edit_keeps_rules(services, anna):
    *_, admin = services
    admin_id, uid, data, muscles = anna
    push = next(w for w in data["workouts"] if w["notes"] == "Push day")
    with pytest.raises(ValueError):  # another workout already on that day
        admin.update_workout(admin_id, uid, push["id"], date(2026, 5, 3), "", [muscles[0]])
    with pytest.raises(ValueError):  # future date
        admin.update_workout(admin_id, uid, push["id"], date(2999, 1, 1), "", [muscles[0]])
    with pytest.raises(ValueError):  # no muscle group
        admin.update_workout(admin_id, uid, push["id"], date(2026, 5, 1), "", [])


def test_admin_deletes_workout(services, anna):
    *_, admin = services
    admin_id, uid, data, _ = anna
    admin.delete_workout(admin_id, uid, data["workouts"][0]["id"])
    assert len(admin.get_user_entries(admin_id, "anna")["workouts"]) == 1


def test_admin_edits_and_deletes_pr(services, anna):
    *_, admin = services
    admin_id, uid, data, _ = anna
    pr_id = data["personal_records"]["Bench Press"][0]["id"]
    admin.update_pr(admin_id, uid, pr_id, 85.0, date(2026, 5, 4))
    pr = admin.get_user_entries(admin_id, "anna")["personal_records"]["Bench Press"][0]
    assert (pr["weight_kg"], pr["date"]) == (85.0, date(2026, 5, 4))

    admin.delete_pr(admin_id, uid, pr_id)
    assert admin.get_user_entries(admin_id, "anna")["personal_records"] == {}


def test_admin_edits_weight_entries_and_goal(services, anna):
    *_, admin = services
    admin_id, uid, data, _ = anna
    newest, older = data["weight_entries"]
    admin.update_weight_entry(admin_id, uid, newest["id"], date(2026, 5, 2), 69.5)
    with pytest.raises(ValueError):  # date already used by the other entry
        admin.update_weight_entry(admin_id, uid, newest["id"], older["date"], 69.5)
    admin.delete_weight_entry(admin_id, uid, older["id"])
    admin.set_weight_goal(admin_id, uid, 67.0)

    after = admin.get_user_entries(admin_id, "anna")
    assert [e["weight_kg"] for e in after["weight_entries"]] == [69.5]
    assert after["weight_goal"] == 67.0


def test_admin_adds_and_deletes_exercise(services, anna):
    *_, admin = services
    admin_id, uid, _, _ = anna
    ex_id = admin.create_exercise(admin_id, uid, "Squat")
    assert "Squat" in [e["name"] for e in admin.get_user_entries(admin_id, "anna")["exercises"]]
    admin.delete_exercise(admin_id, uid, ex_id)
    assert "Squat" not in [e["name"] for e in admin.get_user_entries(admin_id, "anna")["exercises"]]


def test_admin_cannot_edit_entry_of_other_user_via_wrong_id(services, anna):
    auth, workout, _, admin = services
    admin_id, uid, data, muscles = anna
    bob = auth.register("bob", "secret")
    # anna's workout id together with bob's user id must not work
    with pytest.raises(ValueError):
        admin.delete_workout(admin_id, bob, data["workouts"][0]["id"])


def test_normal_user_cannot_edit_via_admin_service(services, anna):
    auth, _, _, admin = services
    _, uid, data, _ = anna
    curious = auth.register("curious", "secret")
    with pytest.raises(PermissionError):
        admin.delete_workout(curious, uid, data["workouts"][0]["id"])
    with pytest.raises(PermissionError):
        admin.set_weight_goal(curious, uid, 50)
