from __future__ import annotations
import os
from pathlib import Path
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from models.base import Base

# Default admin login (override with ADMIN_USERNAME / ADMIN_PASSWORD)
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"

def _database_url() -> str:
    # Put SQLite file into ./data/gym_tracker.db
    data_dir = Path(__file__).resolve().parents[1] / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / "gym_tracker.db"
    return f"sqlite:///{db_path}"

_ENGINE: Engine | None = None

def get_engine() -> Engine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = create_engine(
            _database_url(),
            echo=False,
            future=True,
        )
    return _ENGINE

def init_db() -> None:
    """Create tables and seed default data."""
    engine = get_engine()

    # Import models so SQLAlchemy knows them before create_all()
    from models.user import User  # noqa: F401
    from models.workout_session import WorkoutSession  # noqa: F401
    from models.muscle_group import MuscleGroup  # noqa: F401
    from models.session_muscle import SessionMuscle  # noqa: F401
    from models.exercise import Exercise  # noqa: F401
    from models.personal_record import PersonalRecord  # noqa: F401
    from models.weight_entry import WeightEntry, WeightGoal  # noqa: F401

    Base.metadata.create_all(engine)

    # Existing databases were created before the is_admin column existed.
    # create_all() does not alter tables, so add the column if it is missing.
    _ensure_is_admin_column(engine)

    # Seed muscles once
    from db.session import get_session
    from models.muscle_group import MuscleGroup

    #Muscles to be trained
    default_muscles = [
        ("Legs", "legs"),
        ("Chest", "chest"),
        ("Back", "back"),
        ("Shoulders", "shoulders"),
        ("Biceps", "biceps"),
        ("Triceps", "triceps"),
        ("Abs", "abs"),
    ]

    with get_session() as session:
        if session.query(MuscleGroup).count() == 0:
            session.add_all([MuscleGroup(name=n, svg_key=k) for n, k in default_muscles])
            session.commit()

    _seed_admin_user()


def _ensure_is_admin_column(engine: Engine) -> None:
    columns = {c["name"] for c in inspect(engine).get_columns("users")}
    if "is_admin" not in columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT 0"))


def _seed_admin_user() -> None:
    """
    Create the admin account once. Credentials can be set with the
    environment variables ADMIN_USERNAME and ADMIN_PASSWORD.
    An existing normal user with the same name is never promoted.
    """
    from db.session import get_session
    from models.user import User
    from utils.security import hash_password

    username = os.environ.get("ADMIN_USERNAME", DEFAULT_ADMIN_USERNAME)
    password = os.environ.get("ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD)

    with get_session() as session:
        if session.query(User).filter(User.is_admin.is_(True)).first():
            return
        if session.query(User).filter(User.username == username).first():
            print(f"[init_db] Admin not created: username '{username}' is already taken.")
            return
        session.add(User(username=username, password_hash=hash_password(password), is_admin=True))
        session.commit()