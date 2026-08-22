import os
from datetime import datetime, timedelta

import bcrypt
from jose import jwt


def _secret_key() -> str:
    return os.environ["JWT_SECRET_KEY"]


def _algorithm() -> str:
    return os.getenv("JWT_ALGORITHM", "HS256")


def _expire_minutes() -> int:
    return int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed_password.encode())


def create_access_token(user_id: int, clinic_id: int, role: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=_expire_minutes())
    payload = {"sub": str(user_id), "clinic_id": clinic_id, "role": role, "exp": expire}
    return jwt.encode(payload, _secret_key(), algorithm=_algorithm())


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, _secret_key(), algorithms=[_algorithm()])
