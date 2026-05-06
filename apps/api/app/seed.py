"""Seed test users into the database."""

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User, RoleEnum
from app.core.password import hash_password


def seed_test_users() -> None:
    db: Session = SessionLocal()
    try:
        # Check if users already exist
        existing_student = db.query(User).filter(User.email == "student@test.com").first()
        if existing_student:
            print("Test users already exist, skipping seed.")
            return

        # Create test accounts
        test_accounts = [
            {"email": "student@test.com", "password": "password123456", "role": RoleEnum.student},
            {"email": "teacher@test.com", "password": "password123456", "role": RoleEnum.teacher},
            {"email": "admin@test.com", "password": "password123456", "role": RoleEnum.admin},
        ]

        for account in test_accounts:
            user = User(
                email=account["email"],
                hashed_password=hash_password(account["password"]),
                role=account["role"],
            )
            db.add(user)

        db.commit()
        print(f"✓ Seeded {len(test_accounts)} test users")

    except Exception as e:
        print(f"Error seeding users: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_test_users()
