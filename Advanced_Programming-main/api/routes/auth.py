from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from api.tokens import issue_token
from services.auth_service import AuthService


router = APIRouter(
    prefix="/api/auth",
    tags=["Auth"],
)

auth_service = AuthService()


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    user_id: int
    is_admin: bool


# LOG IN and receive a token for later requests
@router.post("/login", response_model=LoginResponse)
def login(credentials: LoginRequest):
    try:
        user_id = auth_service.login(
            username=credentials.username,
            password=credentials.password,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
        )

    return LoginResponse(
        token=issue_token(user_id),
        user_id=user_id,
        is_admin=auth_service.is_admin(user_id),
    )
