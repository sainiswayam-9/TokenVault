# data_service/jwt_guard.py
# Decodes incoming JWT and provides role-based access control dependencies

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from data_service.config import SECRET_KEY, ALGORITHM
from data_service.models import TokenData

# Extracts Bearer token from Authorization header
bearer_scheme = HTTPBearer()


def decode_token(token: str) -> TokenData:
    """
    Decode and validate a JWT token.
    Returns TokenData with username and role.
    Raises 401 if token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if not username or not role:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload is missing required fields",
            )
        return TokenData(username=username, role=role)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token invalid or expired: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> TokenData:
    """FastAPI dependency: decode token and return current user."""
    return decode_token(credentials.credentials)


def require_role(*allowed_roles: str):
    """
    FastAPI dependency factory.
    Usage: Depends(require_role("manager", "hr"))
    Raises 403 if user's role is not in allowed_roles.
    """
    def role_checker(
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    ) -> TokenData:
        user = decode_token(credentials.credentials)
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {list(allowed_roles)}. Your role: {user.role}",
            )
        return user
    return role_checker
