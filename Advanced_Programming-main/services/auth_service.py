from __future__ import annotations
from db.session import get_session
from models.user import User
from utils.security import hash_password, verify_password

class AuthService:
    def register(self, username: str, password: str) -> int:
        username = (username or "").strip()
        password = password or ""

        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters.")
        if len(password) < 4:
            raise ValueError("Password must be at least 4 characters.")

        with get_session() as session:
            existing = session.query(User).filter(User.username == username).first()
            if existing:
                raise ValueError("Username already exists. Choose another one.")

            # hash and persist the new user record
            user = User(username=username, password_hash=hash_password(password))
            session.add(user)
            session.commit()
            session.refresh(user)  # ensures user.id is loaded
            return user.id

    def login(self, username: str, password: str) -> int:
        username = (username or "").strip()
        password = password or ""

        if not username or not password:
            raise ValueError("Please enter username and password.")

        with get_session() as session:
            user = session.query(User).filter(User.username == username).first()
            if not user:
                raise ValueError("Invalid username or password.")

            if not verify_password(password, user.password_hash):
                raise ValueError("Invalid username or password.")

            return user.id

    def get_user_by_id(self, user_id: int) -> dict[str, str] | None:
        with get_session() as session:
            # load user data for rendering and session validation
            user = session.get(User, user_id)
            if not user:
                return None
            return {"id": user.id, "username": user.username}