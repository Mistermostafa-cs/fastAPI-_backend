from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, profiles, roles, users, student, teacher, parent, admin, academic_v2
from app.api.term_offerings import router as term_offerings_router
from app.api.grade_setup import router as grade_setup_router
from app.core.config import settings
from app.core.errors import register_error_handlers
from app.db.models import prepare_models

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
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
app.include_router(academic_v2.router, prefix=settings.api_prefix)
app.include_router(student.router, prefix=settings.api_prefix)
app.include_router(teacher.router, prefix=settings.api_prefix)
app.include_router(parent.router, prefix=settings.api_prefix)
app.include_router(admin.router, prefix=settings.api_prefix)

# ── New routers ───────────────────────────────────────────────────────────────
app.include_router(term_offerings_router, prefix=settings.api_prefix)
app.include_router(grade_setup_router, prefix=settings.api_prefix)
