try:
    from pydantic_settings import BaseSettings
except ModuleNotFoundError:  # pragma: no cover - local test fallback when deps are unavailable
    class BaseSettings:  # type: ignore[too-many-ancestors]
        def __init__(self, **kwargs):
            for name, value in self.__class__.__dict__.items():
                if name.startswith("_") or callable(value) or isinstance(value, property):
                    continue
                setattr(self, name, kwargs.get(name, value))


class Settings(BaseSettings):
    APP_NAME: str = "Document Intelligence Platform"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    ALLOWED_ORIGINS: str = "*"

    DATABASE_URL: str = "postgresql://docuser:docpass@localhost:5432/documents"
    SQL_ECHO: bool = False

    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: str = "json"
    CELERY_TIMEZONE: str = "UTC"
    CELERY_ENABLE_UTC: bool = True

    CELERY_WORKER_CONCURRENCY: int = 4
    CELERY_WORKER_MAX_TASKS_PER_CHILD: int = 1000
    CELERY_TASK_TIME_LIMIT: int = 600
    CELERY_TASK_SOFT_TIME_LIMIT: int = 540

    CELERY_TASK_MAX_RETRIES: int = 3
    CELERY_TASK_DEFAULT_RETRY_DELAY: int = 60

    ANTHROPIC_API_KEY: str = ""
    AI_MODEL: str = "claude-sonnet-4-20250514"

    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    AI_MAX_TOKENS: int = 4096

    STORAGE_PATH: str = "/app/data"
    UPLOAD_PATH: str = "/app/data/uploads"
    PROCESSED_PATH: str = "/app/data/processed"

    ENABLE_AUTO_CATEGORIZATION: bool = True
    ENABLE_ENTITY_EXTRACTION: bool = True
    CATEGORY_CONFIDENCE_THRESHOLD: float = 0.7
    REVIEW_CONFIDENCE_THRESHOLD: float = 0.75
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_FILE_TYPES: str = "pdf,docx,doc,xlsx,xls,pptx,ppt,txt,jpg,jpeg,png,gif,tiff,bmp"

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def celery_accept_content(self) -> list[str]:
        return [item.strip() for item in self.CELERY_ACCEPT_CONTENT.split(",") if item.strip()]


settings = Settings()
