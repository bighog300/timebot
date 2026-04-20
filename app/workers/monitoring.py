"""Queue and worker monitoring helpers."""

from app.workers.celery_app import celery_app


def inspect_workers(timeout: int = 2) -> dict:
    inspect = celery_app.control.inspect(timeout=timeout)

    active = inspect.active() or {}
    reserved = inspect.reserved() or {}
    scheduled = inspect.scheduled() or {}
    stats = inspect.stats() or {}

    return {
        "workers": list(stats.keys()),
        "active_tasks": sum(len(v) for v in active.values()),
        "reserved_tasks": sum(len(v) for v in reserved.values()),
        "scheduled_tasks": sum(len(v) for v in scheduled.values()),
        "worker_count": len(stats),
    }
