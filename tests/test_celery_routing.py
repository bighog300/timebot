from app.workers.celery_app import celery_app


def test_celery_queue_topology_declares_expected_queues():
    queues = {q.name for q in celery_app.conf.task_queues}
    assert {"ingestion", "ai_analysis", "reports", "maintenance"}.issubset(queues)


def test_celery_task_routes_cover_core_background_domains():
    routes = celery_app.conf.task_routes
    assert routes["app.workers.tasks.process_document_task"]["queue"] == "ingestion"
    assert routes["app.workers.tasks.reprocess_document_task"]["queue"] == "ingestion"
    assert routes["app.workers.tasks.embed_document_task"]["queue"] == "ai_analysis"
    assert routes["app.workers.tasks.detect_relationships_task"]["queue"] == "ai_analysis"
    assert routes["app.workers.tasks.backfill_relationships_task"]["queue"] == "maintenance"
    assert routes["app.workers.tasks.cleanup_old_tasks"]["queue"] == "maintenance"
