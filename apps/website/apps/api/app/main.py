from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers.auth import router as auth_router
from app.routers.health import router as health_router
from app.routers.quiz import router as quiz_router
from app.database import engine
from app.models import Base
from app.seed import seed_test_users


app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(quiz_router)


@app.on_event("startup")
def startup():
    """Run migrations and seed data on app startup."""
    Base.metadata.create_all(bind=engine)
    seed_test_users()


@app.get("/", summary="Service metadata")
def root() -> dict[str, str]:
    return {"service": settings.app_name, "environment": settings.app_env}
