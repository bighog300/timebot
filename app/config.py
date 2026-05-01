from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Document Intelligence Platform"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    ALLOWED_ORIGINS: str = "http://localhost:5174,http://127.0.0.1:5174"

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

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-latest"
    DEFAULT_AI_PROVIDER: str = "openai"
    AI_PROVIDER_FALLBACKS: str = "openai"

    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    AI_MAX_TOKENS: int = 4096
    CHAT_MAX_HISTORY_MESSAGES: int = 6
    CHAT_RETRIEVAL_CACHE_TTL_SECONDS: int = 120

    DATA_DIR: str = "data"
    UPLOAD_DIR: str = "data/uploads"
    ARTIFACT_DIR: str = "data/artifacts"
    STORAGE_PATH: str = "data"
    UPLOAD_PATH: str = "data/uploads"
    PROCESSED_PATH: str = "data/processed"

    ENABLE_AUTO_CATEGORIZATION: bool = True
    ENABLE_ENTITY_EXTRACTION: bool = True
    CATEGORY_CONFIDENCE_THRESHOLD: float = 0.7
    REVIEW_CONFIDENCE_THRESHOLD: float = 0.75
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_FILE_TYPES: str = "pdf,docx,doc,xlsx,xls,pptx,ppt,txt,jpg,jpeg,png,gif,tiff,bmp"

    GOOGLE_OAUTH_CLIENT_ID: str = ""
    GOOGLE_OAUTH_CLIENT_SECRET: str = ""
    GOOGLE_OAUTH_REDIRECT_URI: str = ""
    GOOGLE_OAUTH_SCOPES: str = "openid,email,profile,https://www.googleapis.com/auth/drive.metadata.readonly"
    CONNECTOR_TOKEN_ENCRYPTION_KEY: str = ""

    AUTH_SECRET_KEY: str = "dev-insecure-change-me"
    AUTH_ALGORITHM: str = "HS256"
    AUTH_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    INITIAL_ADMIN_EMAIL: str = ""
    INITIAL_ADMIN_PASSWORD: str = ""
    INITIAL_ADMIN_NAME: str = "Timebot Admin"

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def celery_accept_content(self) -> list[str]:
        return [item.strip() for item in self.CELERY_ACCEPT_CONTENT.split(",") if item.strip()]

    @property
    def google_oauth_scopes(self) -> list[str]:
        return [item.strip() for item in self.GOOGLE_OAUTH_SCOPES.split(",") if item.strip()]

    @property
    def allowed_origins(self) -> list[str]:
        if self.ALLOWED_ORIGINS.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def effective_data_dir(self) -> str:
        return self.DATA_DIR or self.STORAGE_PATH

    @property
    def effective_upload_dir(self) -> str:
        return self.UPLOAD_DIR or self.UPLOAD_PATH

    @property
    def effective_artifact_dir(self) -> str:
        if self.ARTIFACT_DIR:
            return self.ARTIFACT_DIR
        return self.PROCESSED_PATH or f"{self.effective_data_dir}/artifacts"


settings = Settings()
