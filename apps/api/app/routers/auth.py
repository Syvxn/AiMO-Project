from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from app.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

Role = Literal["admin", "teacher", "student"]


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: Role = "student"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
def register(payload: RegisterRequest) -> dict[str, str]:
    # Temporary stub. This will be replaced with real persistence in PostgreSQL.
    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    token = create_access_token(subject=payload.email, role=payload.role)
    return {"access_token": token, "token_type": "bearer", "role": payload.role}


@router.post("/login")
def login(payload: LoginRequest) -> dict[str, str]:
    # Temporary stub. For MVP skeleton, any password with minimum length is accepted.
    if len(payload.password) < 8:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(subject=payload.email, role="student")
    return {"access_token": token, "token_type": "bearer", "role": "student"}
