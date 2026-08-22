from dataclasses import dataclass
from typing import Iterator, Literal

from fastapi import Depends, Header, HTTPException
from jose import JWTError
from sqlalchemy.orm import Session

from api.auth.security import decode_access_token
from db.postgres_models import get_engine, get_session

_ENGINE = None


def get_db() -> Iterator[Session]:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = get_engine()
    session = get_session(_ENGINE)
    try:
        yield session
    finally:
        session.close()


@dataclass
class AuthenticatedUser:
    user_id: int
    clinic_id: int
    role: Literal["staff", "patient"]


def get_current_user(authorization: str = Header(...)) -> AuthenticatedUser:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = decode_access_token(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return AuthenticatedUser(
        user_id=int(payload["sub"]),
        clinic_id=payload["clinic_id"],
        role=payload["role"],
    )


def require_role(*roles: str):
    def _dependency(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Not authorized for this action")
        return user

    return _dependency
