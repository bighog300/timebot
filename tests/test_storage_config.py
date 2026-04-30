from app.config import Settings
from app.services.storage import StorageService


def test_effective_storage_directories_prefer_new_env_vars():
    cfg = Settings(
        DATA_DIR="/app/data",
        UPLOAD_DIR="/app/uploads",
        ARTIFACT_DIR="/app/artifacts",
        STORAGE_PATH="/tmp/legacy-data",
        UPLOAD_PATH="/tmp/legacy-uploads",
        PROCESSED_PATH="/tmp/legacy-processed",
    )
    assert cfg.effective_data_dir == "/app/data"
    assert cfg.effective_upload_dir == "/app/uploads"
    assert cfg.effective_artifact_dir == "/app/artifacts"


def test_storage_service_uses_configured_paths(monkeypatch):
    monkeypatch.setattr("app.services.storage.settings.DATA_DIR", "/tmp/timebot-data")
    monkeypatch.setattr("app.services.storage.settings.UPLOAD_DIR", "/tmp/timebot-uploads")
    monkeypatch.setattr("app.services.storage.settings.ARTIFACT_DIR", "/tmp/timebot-artifacts")

    svc = StorageService()
    assert str(svc.data_path) == "/tmp/timebot-data"
    assert str(svc.upload_path) == "/tmp/timebot-uploads"
    assert str(svc.artifact_path) == "/tmp/timebot-artifacts"
    assert str(svc.text_path).startswith("/tmp/timebot-artifacts")
    assert str(svc.processing_output_path).startswith("/tmp/timebot-artifacts")
