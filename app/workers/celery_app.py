from celery import Celery

from app.config import settings

celery_app = Celery(
    "doc_intelligence",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_concurrency=settings.CELERY_WORKER_CONCURRENCY,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_track_started=True,
    task_routes={
        "app.workers.tasks.process_document_task": {"queue": "documents"},
        "app.workers.tasks.reprocess_document_task": {"queue": "documents"},
        "app.workers.tasks.cleanup_old_tasks": {"queue": "maintenance"},
    },
    beat_schedule={
        "cleanup-old-queue-entries": {
            "task": "app.workers.tasks.cleanup_old_tasks",
            "schedule": 3600.0,
        },
    },
)
