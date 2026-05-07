from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.password import hash_password
from app.database import get_db
from app.models import RoleEnum, User
from app.routers.auth import require_admin, user_role_to_str

router = APIRouter(prefix="/admin", tags=["admin"])

Role = Literal["admin", "teacher", "student"]


class AdminUserResponse(BaseModel):
    id: int
    user_id: str
    email: EmailStr
    role: Role
    created_at: datetime


class UpdateUserRoleRequest(BaseModel):
    role: Role


class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str
    role: Role = "student"


class DeleteUserResponse(BaseModel):
    status: str
    message: str


class AdminStatsResponse(BaseModel):
    total_users: int
    admins: int
    teachers: int
    students: int


@router.post("/users", response_model=AdminUserResponse)
def create_user(
    payload: CreateUserRequest,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminUserResponse:
    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user is not None:
        raise HTTPException(status_code=409, detail="Email already registered")

    # `require_admin` already ensures only admins can create admin accounts.
    new_user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=RoleEnum(payload.role),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return AdminUserResponse(
        id=new_user.id,
        user_id=new_user.public_user_id,
        email=new_user.email,
        role=user_role_to_str(new_user.role),
        created_at=new_user.created_at,
    )


@router.get("/users", response_model=list[AdminUserResponse])
def list_users(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[AdminUserResponse]:
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [
        AdminUserResponse(
            id=user.id,
            user_id=user.public_user_id,
            email=user.email,
            role=user_role_to_str(user.role),
            created_at=user.created_at,
        )
        for user in users
    ]


@router.get("/stats", response_model=AdminStatsResponse)
def get_admin_stats(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminStatsResponse:
    total_users = db.query(User).count()
    admins = db.query(User).filter(User.role == RoleEnum.admin).count()
    teachers = db.query(User).filter(User.role == RoleEnum.teacher).count()
    students = db.query(User).filter(User.role == RoleEnum.student).count()

    return AdminStatsResponse(
        total_users=total_users,
        admins=admins,
        teachers=teachers,
        students=students,
    )


@router.patch("/users/{user_id}/role", response_model=AdminUserResponse)
def update_user_role(
    user_id: int,
    payload: UpdateUserRoleRequest,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminUserResponse:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = RoleEnum(payload.role)
    db.commit()
    db.refresh(user)

    return AdminUserResponse(
        id=user.id,
        user_id=user.public_user_id,
        email=user.email,
        role=user_role_to_str(user.role),
        created_at=user.created_at,
    )


@router.delete("/users/{user_id}", response_model=DeleteUserResponse)
def delete_user(
    user_id: int,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> DeleteUserResponse:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == current_admin.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")

    user_role = user_role_to_str(user.role)
    if user_role == "admin":
        admin_count = db.query(User).filter(User.role == RoleEnum.admin).count()
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot delete the last admin account")

    db.delete(user)
    db.commit()

    return DeleteUserResponse(status="deleted", message=f"Deleted user {user.email}")