import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import settings
from app.db.base import SessionLocal
from app.api.v1 import (
    action_items,
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
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: schema is managed by Alembic (create_all only when ALEMBIC_SKIP=true).
    from app.db.base import init_db
    # Import models so metadata is available for optional fallback init_db paths
    import app.models  # noqa: F401

    if settings.AUTH_SECRET_KEY == "dev-insecure-change-me":
        logger.warning("AUTH_SECRET_KEY is using the insecure development default. Set a unique secret for shared/prod environments.")

    init_db()

    from app.services.admin_seed import seed_initial_admin

    db = SessionLocal()
    try:
        seed_initial_admin(db)
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
async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled server exception", exc_info=True)
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
