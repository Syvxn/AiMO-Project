from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt
from pydantic import BaseModel

from app.core.config import settings


class TokenData(BaseModel):
    email: str
    role: str


def create_access_token(email: str, role: str) -> str:
    expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"sub": email, "role": role, "exp": expire}
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> Optional[TokenData]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        if email is None:
            return None
        return TokenData(email=email, role=role)
    except Exception:
        return None
