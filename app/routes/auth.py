# app/routes/auth.py
# POST /auth/login — authenticate and get a JWT

from fastapi import APIRouter, HTTPException, status, Request
from app.models import LoginRequest, TokenResponse
from app.auth import verify_password, create_access_token
from app.db import get_user_by_username

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
async def login(request: Request, body: LoginRequest):
    """
    Authenticate with username + password.
    Returns a signed JWT containing username and role.
    """
    db   = request.app.db
    user = await get_user_by_username(db, body.username)

    if not user or not verify_password(body.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Account is disabled")

    token = create_access_token({"sub": user["username"], "role": user["role"]})
    return TokenResponse(
        access_token=token,
        role=user["role"],
        username=user["username"],
    )
