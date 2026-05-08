from sqlalchemy import Column, Integer, String, Enum as SQLEnum, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime
from uuid import uuid4
import enum

Base = declarative_base()


class RoleEnum(str, enum.Enum):
    admin = "admin"
    teacher = "teacher"
    student = "student"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    public_user_id = Column(String(36), unique=True, index=True, nullable=False, default=lambda: str(uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLEnum(RoleEnum), default=RoleEnum.student, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return (
            f"<User(id={self.id}, public_user_id={self.public_user_id}, "
            f"email={self.email}, role={self.role})>"
        )


class StudyMaterial(Base):
    __tablename__ = "study_materials"

    id = Column(Integer, primary_key=True, index=True)
    original_filename = Column(String, nullable=False)
    description = Column(String, nullable=False, default="")
    storage_filename = Column(String, unique=True, nullable=False)
    content_type = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    uploaded_by_user_id = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return (
            "<StudyMaterial(id={id}, original_filename={name}, uploaded_by={user})>".format(
                id=self.id,
                name=self.original_filename,
                user=self.uploaded_by_user_id,
            )
        )
