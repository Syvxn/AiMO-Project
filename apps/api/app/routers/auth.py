from typing import Literal

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.security import create_access_token, decode_token, TokenData
from app.core.password import hash_password, verify_password
from app.models import User
from app.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

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


def get_current_user(token: str, db: Session = Depends(get_db)) -> TokenData:
    """Dependency to extract and validate JWT token from Authorization header."""
    credentials_exception = HTTPException(status_code=401, detail="Invalid credentials")
    token_data = decode_token(token)
    if token_data is None:
        raise credentials_exception
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return token_data


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

    token = create_access_token(email=user.email, role=user.role.value)
    return AuthResponse(access_token=token, token_type="bearer", role=user.role.value)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(email=user.email, role=user.role.value)
    return AuthResponse(access_token=token, token_type="bearer", role=user.role.value)
