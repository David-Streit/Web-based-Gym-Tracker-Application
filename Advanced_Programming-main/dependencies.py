"""Request authentication for the initial FastAPI integration.

HTTP Basic is intentionally limited to a local/course MVP. Deploy only behind
HTTPS and migrate to session/token authentication before public release.
"""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from services.auth_service import AuthService

security = HTTPBasic()
auth_service = AuthService()


def current_user_id(credentials: Annotated[HTTPBasicCredentials, Depends(security)]) -> int:
    try:
        user_id = auth_service.login(credentials.username, credentials.password)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Basic"},
        ) from None
    if auth_service.is_admin(user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins cannot manage workouts")
    return user_id
