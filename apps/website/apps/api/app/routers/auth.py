from typing import Literal

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.security import create_access_token, decode_token
from app.core.password import hash_password, verify_password
from app.models import User
from app.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)

Role = Literal["admin", "teacher", "student"]


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: Role = "student"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    role: str


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Dependency to extract and validate JWT token from Authorization header."""
    credentials_exception = HTTPException(status_code=401, detail="Invalid credentials")
    if credentials is None:
        raise credentials_exception

    token_data = decode_token(credentials.credentials)
    if token_data is None:
        raise credentials_exception

    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency that ensures the current user has admin role."""
    if user_role_to_str(current_user.role) != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def user_role_to_str(role_value: str | object) -> str:
    """Normalize role enum/value to plain string for comparisons and responses."""
    return role_value.value if hasattr(role_value, "value") else str(role_value)


@router.post("/register", response_model=AuthResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")

    hashed_pwd = hash_password(payload.password)
    user = User(email=payload.email, hashed_password=hashed_pwd, role=payload.role)
    db.add(user)
    db.commit()
    db.refresh(user)

    role_value = user_role_to_str(user.role)
    token = create_access_token(email=user.email, role=role_value)
    return AuthResponse(access_token=token, token_type="bearer", role=role_value)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    role_value = user_role_to_str(user.role)
    token = create_access_token(email=user.email, role=role_value)
    return AuthResponse(access_token=token, token_type="bearer", role=role_value)
