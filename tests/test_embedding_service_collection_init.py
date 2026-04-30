from app.services.embedding_service import EmbeddingService


def test_ensure_collection_tolerates_already_exists(monkeypatch):
    service = EmbeddingService.__new__(EmbeddingService)
    service.embedding_dim = 1536
    service.collection_name = "documents"

    class _QdrantStub:
        def get_collection(self, _name):
            raise RuntimeError("not found")

        def create_collection(self, **_kwargs):
            raise RuntimeError("409 Collection already exists")

    service.qdrant = _QdrantStub()

    service._ensure_collection()

