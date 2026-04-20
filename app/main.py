from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.api.v1 import analysis, categories, connections, documents, insights, queue, search, upload, websocket


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create all tables (safe to call multiple times)
    from app.db.base import init_db
    # Import all models so SQLAlchemy registers them before create_all
    import app.models  # noqa: F401

    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="AI-powered document processing and intelligence platform",
    lifespan=lifespan,
)

origins = settings.ALLOWED_ORIGINS.split(",") if settings.ALLOWED_ORIGINS != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
app.include_router(upload.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1")
app.include_router(queue.router, prefix="/api/v1")
app.include_router(websocket.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(insights.router, prefix="/api/v1")
app.include_router(connections.router, prefix="/api/v1")


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
