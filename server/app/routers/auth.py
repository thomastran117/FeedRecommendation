import uuid

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from app import database, security

router = APIRouter()


class SignupRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: SignupRequest):
    if database.get_user_by_email(body.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user_id = str(uuid.uuid4())
    hashed = security.hash_password(body.password)
    database.create_user(user_id, body.email, hashed)

    return TokenResponse(
        access_token=security.create_access_token(user_id),
        refresh_token=await security.create_refresh_token(user_id),
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    user = database.get_user_by_email(body.email)
    if not user or not security.verify_password(body.password, user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    return TokenResponse(
        access_token=security.create_access_token(user["id"]),
        refresh_token=await security.create_refresh_token(user["id"]),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest):
    try:
        access_token, refresh_token = await security.rotate_refresh_token(body.refresh_token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: RefreshRequest):
    try:
        await security.revoke_refresh_token(body.refresh_token)
    except Exception:
        pass  # already expired or invalid — treat as success
