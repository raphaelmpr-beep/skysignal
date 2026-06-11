"""
JWT authentication utilities for SkySignal.
Supports SKIP_AUTH=true dev bypass.
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production-!!!")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24h
SKIP_AUTH = os.getenv("SKIP_AUTH", "false").lower() == "true"

def _strip_unicode_ws(s: str) -> str:
    """Strip all Unicode whitespace variants (including U+2009 thin space from mobile paste)."""
    return re.sub(r'^[\s\u00a0\u2000-\u200f\u2028\u2029\u202f\u205f\u3000\ufeff]+|[\s\u00a0\u2000-\u200f\u2028\u2029\u202f\u205f\u3000\ufeff]+$', '', s)

DEV_ORG_ID = _strip_unicode_ws(os.getenv("DEV_ORG_ID", "00000000-0000-0000-0000-000000000001"))
DEV_USER_ID = _strip_unicode_ws(os.getenv("DEV_USER_ID", "00000000-0000-0000-0000-000000000002"))

DEV_USER = {
    "sub": DEV_USER_ID,
    "user_id": DEV_USER_ID,
    "org_id": DEV_ORG_ID,
    "email": "dev@skysignal.local",
    "role": "admin",
    "full_name": "Dev User",
}

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> dict:
    """
    Returns the current user dict from JWT.
    If SKIP_AUTH=true, returns a hardcoded dev user without token validation.
    """
    if SKIP_AUTH:
        return DEV_USER

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_token(token)

    user_id = payload.get("sub") or payload.get("user_id")
    org_id = payload.get("org_id")
    if not user_id or not org_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "sub": user_id,
        "user_id": user_id,
        "org_id": org_id,
        "email": payload.get("email", ""),
        "role": payload.get("role", "analyst"),
        "full_name": payload.get("full_name", ""),
    }


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("role") not in ("admin",):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return current_user
