from fastapi import APIRouter, Depends, HTTPException, Response
from jose import JWTError

from app.dependencies.auth import get_current_user
from app.domain.user import InvalidCredentialsError, InvalidTokenError, UserAlreadyExistsError
from app.infrastructure.redis import get_redis
from app.infrastructure.repositories import user_repo_factory
from app.models import User
from app.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

_auth_service = AuthService(user_repo_factory=user_repo_factory, redis=get_redis())


def _to_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else "",
    )


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(body: RegisterRequest) -> UserResponse:
    try:
        user = await _auth_service.register(
            username=body.username,
            email=body.email,
            password=body.password,
        )
        return _to_user_response(user)
    except UserAlreadyExistsError:
        raise HTTPException(status_code=409, detail="Username or email already exists")


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest) -> TokenResponse:
    try:
        access_token, refresh_token = await _auth_service.login(
            username=body.username,
            password=body.password,
        )
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)
    except InvalidCredentialsError:
        raise HTTPException(status_code=401, detail="Invalid username or password")


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(body: RefreshRequest) -> AccessTokenResponse:
    try:
        access_token = await _auth_service.refresh(body.refresh_token)
        return AccessTokenResponse(access_token=access_token)
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/logout", status_code=204)
async def logout(current_user: User = Depends(get_current_user)) -> Response:
    await _auth_service.logout(current_user.username)
    return Response(status_code=204)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return _to_user_response(current_user)
