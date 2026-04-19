from pydantic_settings import BaseSettings
from typing import Optional


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
    CELERY_WORKER_CONCURRENCY: int = 4
    CELERY_TASK_MAX_RETRIES: int = 3

    ANTHROPIC_API_KEY: str = ""
    AI_MODEL: str = "claude-sonnet-4-6"
    AI_MAX_TOKENS: int = 4096

    STORAGE_PATH: str = "/app/data"
    UPLOAD_PATH: str = "/app/data/uploads"
    PROCESSED_PATH: str = "/app/data/processed"

    ENABLE_AUTO_CATEGORIZATION: bool = True
    ENABLE_ENTITY_EXTRACTION: bool = True
    CATEGORY_CONFIDENCE_THRESHOLD: float = 0.7
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_FILE_TYPES: str = "pdf,docx,doc,xlsx,xls,pptx,ppt,txt,jpg,jpeg,png,gif,tiff,bmp"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
