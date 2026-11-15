from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBasic,
    HTTPBasicCredentials,
    HTTPBearer,
)

from api.tokens import user_id_for_token
from services.auth_service import AuthService


# auto_error=False: we check both schemes ourselves and return one clear 401
basic_scheme = HTTPBasic(auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)
auth_service = AuthService()


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def current_user_id(
    bearer: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    basic: HTTPBasicCredentials | None = Depends(basic_scheme),
) -> int:
    """Return the logged-in user's id.

    Accepts a Bearer token from POST /api/auth/login (used by the web
    interface) or HTTP Basic credentials (handy for testing in /docs).
    """
    user_id: int | None = None

    if bearer is not None:
        user_id = user_id_for_token(bearer.credentials)
        if user_id is None:
            raise _unauthorized("Session expired or invalid token. Please log in again.")
    elif basic is not None:
        try:
            user_id = auth_service.login(
                username=basic.username,
                password=basic.password,
            )
        except ValueError:
            raise _unauthorized("Invalid username or password")
    else:
        raise _unauthorized("Not authenticated")

    # Workout endpoints are only for regular users
    if auth_service.is_admin(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin accounts cannot track workouts",
        )

    return user_id
