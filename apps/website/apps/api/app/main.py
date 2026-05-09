from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers.admin import router as admin_router
from app.routers.auth import router as auth_router
from app.routers.health import router as health_router
from app.routers.npc_chat import router as npc_chat_router
from app.routers.quiz import router as quiz_router
from app.routers.teacher import router as teacher_router
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
app.include_router(admin_router)
app.include_router(teacher_router)
app.include_router(npc_chat_router)


@app.on_event("startup")
def startup():
    """Seed data on app startup after migrations have been applied."""
    seed_test_users()


@app.get("/", summary="Service metadata")
def root() -> dict[str, str]:
    return {"service": settings.app_name, "environment": settings.app_env}
