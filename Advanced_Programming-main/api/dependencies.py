
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from services.auth_service import AuthService


security = HTTPBasic()
auth_service = AuthService()


def current_user_id(
    credentials: HTTPBasicCredentials = Depends(security),
) -> int:
    try:
        user_id = auth_service.login(
            username=credentials.username,
            password=credentials.password,
        )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    # Workout endpoints are only for regular users
    if auth_service.is_admin(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin accounts cannot track workouts",
        )

    return user_id
