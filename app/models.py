# app/models.py
# All Pydantic models in one place — request/response validation

from pydantic import BaseModel, Field
from typing import Optional, List


# ── Auth / JWT ────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


class TokenData(BaseModel):
    """Decoded JWT payload passed between dependencies."""
    username: str
    role: str


# ── User ──────────────────────────────────────────────────────────────────────

class UserInDB(BaseModel):
    username: str
    hashed_password: str
    role: str
    is_active: bool = True


class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)
    role: str


class UpdateUserRequest(BaseModel):
    """All fields optional — only send what you want to change."""
    password: Optional[str] = Field(None, min_length=6)
    role:      Optional[str] = None
    is_active: Optional[bool] = None


# ── Role ──────────────────────────────────────────────────────────────────────

class CreateRoleRequest(BaseModel):
    name:        str        = Field(..., min_length=2)
    permissions: List[str]  = []


class UpdateRoleRequest(BaseModel):
    permissions: List[str]


# ── Permission ────────────────────────────────────────────────────────────────

class CreatePermissionRequest(BaseModel):
    key:         str = Field(..., min_length=2)
    description: str = Field(..., min_length=5)
