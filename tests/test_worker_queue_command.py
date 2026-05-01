from pathlib import Path


def test_docker_compose_worker_listens_on_new_task_queues():
    compose = Path('docker-compose.yml').read_text()
    assert '-Q ingestion,ai_analysis,maintenance' in compose
    assert '-Q documents,maintenance' not in compose
