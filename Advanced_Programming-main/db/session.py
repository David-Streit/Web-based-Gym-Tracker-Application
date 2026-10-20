from __future__ import annotations
from contextlib import contextmanager
from typing import Iterator
from sqlalchemy.orm import Session, sessionmaker
from db.engine import get_engine

SessionLocal = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, future=True)

@contextmanager
def get_session() -> Iterator[Session]:
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()