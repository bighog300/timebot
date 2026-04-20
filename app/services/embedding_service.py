import logging
from typing import Dict, List, Optional

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generate and store embeddings in Qdrant."""

    def __init__(self):
        self.embedding_dim = 384
        self.collection_name = "documents"
        self._enabled = True

        try:
            from qdrant_client import QdrantClient
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            self.qdrant = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
            self._ensure_collection()
        except Exception as exc:
            logger.warning("Embedding service initialization failed: %s", exc)
            self._enabled = False
            self.model = None
            self.qdrant = None

    def _ensure_collection(self):
        from qdrant_client.models import Distance, VectorParams

        try:
            self.qdrant.get_collection(self.collection_name)
        except Exception:
            self.qdrant.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.embedding_dim, distance=Distance.COSINE),
            )

    @property
    def enabled(self) -> bool:
        return self._enabled

    def generate_embedding(self, text: str) -> List[float]:
        if not self.enabled:
            return [0.0] * self.embedding_dim
        if not text:
            return [0.0] * self.embedding_dim
        return self.model.encode(text[:5000], convert_to_numpy=True).tolist()

    def store_document_embedding(self, document_id: str, text: str, metadata: Optional[Dict] = None):
        if not self.enabled:
            logger.warning("Embedding service unavailable; skipping storage for %s", document_id)
            return

        from qdrant_client.models import PointStruct

        point = PointStruct(id=document_id, vector=self.generate_embedding(text), payload=metadata or {})
        self.qdrant.upsert(collection_name=self.collection_name, points=[point])

    def semantic_search(self, query: str, limit: int = 10, score_threshold: float = 0.5) -> List[Dict]:
        if not self.enabled:
            return []

        results = self.qdrant.search(
            collection_name=self.collection_name,
            query_vector=self.generate_embedding(query),
            limit=limit,
            score_threshold=score_threshold,
        )

        return [
            {"document_id": str(result.id), "score": result.score, "metadata": result.payload}
            for result in results
        ]

    def find_similar_documents(self, document_id: str, limit: int = 5) -> List[Dict]:
        if not self.enabled:
            return []

        try:
            doc = self.qdrant.retrieve(collection_name=self.collection_name, ids=[document_id], with_vectors=True)
            doc_vector = doc[0].vector
        except Exception:
            return []

        results = self.qdrant.search(
            collection_name=self.collection_name,
            query_vector=doc_vector,
            limit=limit + 1,
        )

        output = []
        for result in results:
            if str(result.id) != document_id:
                output.append(
                    {"document_id": str(result.id), "score": result.score, "metadata": result.payload}
                )
        return output[:limit]

    def delete_document_embedding(self, document_id: str):
        if not self.enabled:
            return
        self.qdrant.delete(collection_name=self.collection_name, points_selector=[document_id])


embedding_service = EmbeddingService()
