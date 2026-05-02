import logging
from typing import Dict, List, Optional

from app.config import settings
from app.services.openai_client import APIError, openai_client_service

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generate and store embeddings in Qdrant."""

    def __init__(self):
        self.embedding_dim = 1536
        self.collection_name = "documents"
        self._enabled = True

        if not openai_client_service.enabled:
            logger.warning("OPENAI_API_KEY not configured; semantic embedding disabled")
            self._enabled = False
            self.qdrant = None
            return

        try:
            from qdrant_client import QdrantClient

            self.qdrant = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
            self._ensure_collection()
        except Exception as exc:
            logger.warning("Embedding service initialization failed: %s", exc)
            self._enabled = False
            self.qdrant = None

    def _ensure_collection(self):
        from qdrant_client.models import Distance, VectorParams

        try:
            self.qdrant.get_collection(self.collection_name)
            return
        except Exception:
            pass

        try:
            self.qdrant.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.embedding_dim, distance=Distance.COSINE),
            )
        except Exception as exc:
            if "already exists" in str(exc).lower():
                logger.info("Qdrant collection already exists; continuing initialization")
                return
            raise

    @property
    def enabled(self) -> bool:
        return self._enabled

    def generate_embedding(self, text: str) -> List[float]:
        if not self.enabled or not text:
            return [0.0] * self.embedding_dim
        try:
            embedding = openai_client_service.generate_embedding(
                model=settings.OPENAI_EMBEDDING_MODEL,
                input_text=text[:8000],
            )
            if len(embedding) != self.embedding_dim:
                logger.warning(
                    "Embedding size mismatch: expected=%s got=%s. Updating runtime dimension.",
                    self.embedding_dim,
                    len(embedding),
                )
                self.embedding_dim = len(embedding)
            return embedding
        except APIError as e:
            logger.error("OpenAI embedding API error: %s", e)
        except Exception as e:
            logger.error("Embedding generation failed: %s", e)
        return [0.0] * self.embedding_dim

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
