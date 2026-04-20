"""Helpers for periodic queue maintenance jobs."""

from app.workers.tasks import cleanup_old_tasks


def run_cleanup_now() -> str:
    """Trigger queue cleanup outside of celery beat (best effort utility)."""
    result = cleanup_old_tasks.delay()
    return result.id
