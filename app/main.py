import logging
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import settings
from app.db.base import SessionLocal
from app.api.v1 import (
    action_items,
    admin,
    analysis,
    auth,
    categories,
    connections,
    documents,
    insights,
    queue,
    review,
    search,
    upload,
    websocket,
    chat,
    reports,
    gmail_imports,
    monetization,
)

logger = logging.getLogger(__name__)

_INSECURE_DEFAULT_AUTH_SECRET = "dev-insecure-change-me"
_PRODUCTION_LIKE_ENVS = {"production", "prod", "staging"}
_KNOWN_INSECURE_AUTH_SECRETS = {
    "",
    _INSECURE_DEFAULT_AUTH_SECRET,
    "changeme",
    "change-me",
    "replace-me",
    "your-secret-key",
    "secret",
    "default",
}


def _is_production_environment() -> bool:
    return (settings.APP_ENV or "").strip().lower() in _PRODUCTION_LIKE_ENVS


def _validate_auth_secret_for_environment() -> None:
    secret = (settings.AUTH_SECRET_KEY or "").strip()
    normalized = secret.lower()
    if _is_production_environment() and normalized in _KNOWN_INSECURE_AUTH_SECRETS:
        raise RuntimeError(
            "AUTH_SECRET_KEY is required and must not use a development placeholder when APP_ENV is prod/production/staging"
        )
    if normalized == _INSECURE_DEFAULT_AUTH_SECRET:
        logger.warning("AUTH_SECRET_KEY is using the insecure development default. Set a unique secret for shared/prod environments.")


def _sanitize_headers_for_log(headers: dict[str, str]) -> dict[str, str]:
    sanitized: dict[str, str] = {}
    for key, value in headers.items():
        if key.lower() == "authorization":
            sanitized[key] = "[redacted]"
            continue
        sanitized[key] = value
    return sanitized


def _redact_database_url(url: str) -> str:
    parts = urlsplit(url)
    if "@" not in parts.netloc:
        return url
    credentials, host = parts.netloc.rsplit("@", 1)
    username = credentials.split(":", 1)[0] if ":" in credentials else credentials
    return urlunsplit((parts.scheme, f"{username}:***@{host}", parts.path, parts.query, parts.fragment))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: schema is managed by Alembic (create_all only when ALEMBIC_SKIP=true).
    from app.db.base import init_db
    # Import models so metadata is available for optional fallback init_db paths
    import app.models  # noqa: F401

    _validate_auth_secret_for_environment()

    init_db()
    data_dir = Path(settings.effective_data_dir)
    upload_dir = Path(settings.effective_upload_dir)
    artifact_dir = Path(settings.effective_artifact_dir)
    for directory in [data_dir, upload_dir, artifact_dir]:
        directory.mkdir(parents=True, exist_ok=True)
    logger.info("Storage config: database=%s", _redact_database_url(settings.DATABASE_URL))
    logger.info("Storage config: data_dir=%s exists=%s", data_dir, data_dir.exists())
    logger.info("Storage config: upload_dir=%s exists=%s", upload_dir, upload_dir.exists())
    logger.info("Storage config: artifact_dir=%s exists=%s", artifact_dir, artifact_dir.exists())
    logger.info(
        "OpenAI configured: %s; model=%s",
        bool(settings.OPENAI_API_KEY),
        settings.OPENAI_MODEL,
    )

    from app.services.admin_seed import seed_initial_admin
    from app.services.prompt_templates import seed_default_prompt_templates

    db = SessionLocal()
    try:
        seed_initial_admin(db)
        if settings.SEED_DEFAULT_PROMPTS:
            seeded = seed_default_prompt_templates(db)
            logger.info("default_prompt_templates_seeded count=%s", seeded)
    finally:
        db.close()

    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="AI-powered document processing and intelligence platform",
    lifespan=lifespan,
)

origins = settings.allowed_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "Unhandled server exception method=%s path=%s headers=%s exc_type=%s",
        request.method,
        request.url.path,
        _sanitize_headers_for_log(dict(request.headers)),
        type(exc).__name__,
    )
    return JSONResponse(status_code=500, content={"detail": "An unexpected error occurred"})


app.include_router(documents.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
app.include_router(upload.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1")
app.include_router(queue.router, prefix="/api/v1")
app.include_router(websocket.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(insights.router, prefix="/api/v1")
app.include_router(connections.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(review.router, prefix="/api/v1")
app.include_router(action_items.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(gmail_imports.router, prefix="/api/v1")
app.include_router(monetization.router, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health_check():
    from app.db.base import engine

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    return {
        "status": "healthy",
        "service": "doc-intelligence-platform",
        "version": settings.VERSION,
        "database": db_status,
    }


@app.get("/", tags=["root"])
def root():
    return {
        "message": "Document Intelligence Platform API",
        "docs": "/docs",
        "health": "/health",
        "version": settings.VERSION,
    }
