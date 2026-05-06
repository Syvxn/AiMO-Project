from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import RoleEnum, User
from app.routers.auth import require_admin, user_role_to_str

router = APIRouter(prefix="/admin", tags=["admin"])

Role = Literal["admin", "teacher", "student"]


class AdminUserResponse(BaseModel):
    id: int
    email: EmailStr
    role: Role
    created_at: datetime


class UpdateUserRoleRequest(BaseModel):
    role: Role


class AdminStatsResponse(BaseModel):
    total_users: int
    admins: int
    teachers: int
    students: int


@router.get("/users", response_model=list[AdminUserResponse])
def list_users(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[AdminUserResponse]:
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [
        AdminUserResponse(
            id=user.id,
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
        email=user.email,
        role=user_role_to_str(user.role),
        created_at=user.created_at,
    )