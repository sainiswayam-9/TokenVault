# auth_service/models.py
# Pydantic models for request/response validation

from pydantic import BaseModel, Field
from typing import Optional, List


# ── Auth ─────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


# ── User ─────────────────────────────────────────────────────────

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
    """All fields optional — send only what you want to change."""
    password: Optional[str] = Field(None, min_length=6)
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """Safe user shape — never exposes hashed_password."""
    username: str
    role: str
    is_active: bool


# ── Role ─────────────────────────────────────────────────────────

class RoleInDB(BaseModel):
    name: str
    permissions: List[str]


class CreateRoleRequest(BaseModel):
    name: str = Field(..., min_length=2)
    permissions: List[str] = []


class UpdateRoleRequest(BaseModel):
    permissions: List[str]


# ── Permission ───────────────────────────────────────────────────

class PermissionInDB(BaseModel):
    key: str
    description: str


class CreatePermissionRequest(BaseModel):
    key: str = Field(..., min_length=2)
    description: str = Field(..., min_length=5)
