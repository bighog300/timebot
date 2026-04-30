from celery import Celery
import logging

from app.config import settings

logger = logging.getLogger(__name__)

celery_app = Celery(
    "doc_intelligence",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"],
)

logger.info(
    "Celery OpenAI configured: %s; model=%s",
    bool(settings.OPENAI_API_KEY),
    settings.OPENAI_MODEL,
)

celery_app.conf.update(
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    accept_content=settings.celery_accept_content,
    result_serializer=settings.CELERY_RESULT_SERIALIZER,
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=settings.CELERY_ENABLE_UTC,
    worker_concurrency=settings.CELERY_WORKER_CONCURRENCY,
    worker_max_tasks_per_child=settings.CELERY_WORKER_MAX_TASKS_PER_CHILD,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_track_started=True,
    task_default_priority=5,
    result_expires=3600,
    task_routes={
        "app.workers.tasks.process_document_task": {"queue": "documents"},
        "app.workers.tasks.reprocess_document_task": {"queue": "documents"},
        "app.workers.tasks.embed_document_task": {"queue": "documents"},
        "app.workers.tasks.cleanup_old_tasks": {"queue": "maintenance"},
    },
    beat_schedule={
        "cleanup-old-queue-entries": {
            "task": "app.workers.tasks.cleanup_old_tasks",
            "schedule": 3600.0,
        },
    },
)
