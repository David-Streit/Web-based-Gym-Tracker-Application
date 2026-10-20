from __future__ import annotations
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from models.base import Base

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