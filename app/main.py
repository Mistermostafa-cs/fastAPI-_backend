from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import academics, auth, profiles, roles, users, student, teacher, parent, admin
from app.core.config import settings
from app.core.errors import register_error_handlers
from app.db.models import prepare_models

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5041", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)


@app.on_event("startup")
def startup_event() -> None:
    prepare_models()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(users.router, prefix=settings.api_prefix)
app.include_router(roles.router, prefix=settings.api_prefix)
app.include_router(profiles.router, prefix=settings.api_prefix)
app.include_router(academics.router, prefix=settings.api_prefix)
app.include_router(student.router, prefix=settings.api_prefix)
app.include_router(teacher.router, prefix=settings.api_prefix)
app.include_router(parent.router, prefix=settings.api_prefix)
app.include_router(admin.router, prefix=settings.api_prefix)
