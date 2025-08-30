# app/routers/auth.py
from fastapi import APIRouter, status
from app.models import SignupRequest, LoginRequest, RefreshRequest, AuthResponse

router = APIRouter()

@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(body: SignupRequest):
    # TODO: persist user and hash password
    return AuthResponse(access_token="access.demo", refresh_token="refresh.demo")

@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest):
    # TODO: verify credentials
    return AuthResponse(access_token="access.demo", refresh_token="refresh.demo")

@router.post("/refresh", response_model=AuthResponse)
def refresh(body: RefreshRequest):
    # TODO: verify refresh token
    return AuthResponse(access_token="access.demo", refresh_token="refresh.demo")

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout():
    # TODO: revoke refresh token
    return None