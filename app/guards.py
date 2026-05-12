# app/guards.py
# FastAPI dependencies for JWT decoding and role-based access control

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.config import SECRET_KEY, ALGORITHM
from app.models import TokenData

_bearer = HTTPBearer()


def _decode_token(token: str) -> TokenData:
    """Decode and validate a JWT. Raises 401 on failure."""
    try:
        payload  = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role     = payload.get("role")
        if not username or not role:
            raise HTTPException(status_code=401, detail="Token payload missing required fields")
        return TokenData(username=username, role=role)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token invalid or expired: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
) -> TokenData:
    """Decode token and return the current user (any valid role)."""
    return _decode_token(creds.credentials)


def require_role(*allowed_roles: str):
    """
    Dependency factory — restricts endpoint to specific roles.
    Usage: Depends(require_role("manager", "hr"))
    """
    def checker(
        creds: HTTPAuthorizationCredentials = Depends(_bearer),
    ) -> TokenData:
        user = _decode_token(creds.credentials)
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required: {list(allowed_roles)}. Your role: {user.role}",
            )
        return user
    return checker
