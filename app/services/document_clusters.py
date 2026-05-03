from collections import Counter, defaultdict
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.relationships import DocumentRelationship


class DocumentClusterService:
    def list_clusters_for_user(self, db: Session, *, user_id) -> list[dict]:
        documents = db.query(Document).filter(Document.user_id == user_id).all()
        return self._build_clusters(db, documents)

    def list_clusters_for_workspace(self, db: Session, *, workspace_id: UUID) -> list[dict]:
        documents = db.query(Document).filter(Document.workspace_id == workspace_id).all()
        return self._build_clusters(db, documents)

    def _build_clusters(self, db: Session, documents: list[Document]) -> list[dict]:
        if not documents:
            return []

        docs_by_id = {str(doc.id): doc for doc in documents}
        adjacency: dict[str, set[str]] = {doc_id: set() for doc_id in docs_by_id}
        component_signals: defaultdict[frozenset[str], Counter] = defaultdict(Counter)

        document_ids = [doc.id for doc in documents]
        relationships = (
            db.query(DocumentRelationship)
            .filter(
                DocumentRelationship.source_doc_id.in_(document_ids),
                DocumentRelationship.target_doc_id.in_(document_ids),
            )
            .all()
        )

        for rel in relationships:
            source_id = str(rel.source_doc_id)
            target_id = str(rel.target_doc_id)
            if source_id not in adjacency or target_id not in adjacency:
                continue
            adjacency[source_id].add(target_id)
            adjacency[target_id].add(source_id)
            explanation = (rel.relationship_metadata or {}).get("explanation", {})
            for signal in explanation.get("signals", []) or []:
                if isinstance(signal, str):
                    component_signals[frozenset((source_id, target_id))][signal] += 1

        visited: set[str] = set()
        clusters: list[dict] = []
        for start_id in sorted(adjacency.keys()):
            if start_id in visited:
                continue
            stack = [start_id]
            component: list[str] = []
            while stack:
                current = stack.pop()
                if current in visited:
                    continue
                visited.add(current)
                component.append(current)
                stack.extend(sorted(adjacency[current] - visited))

            component_set = set(component)
            relationship_count = 0
            signal_counter: Counter = Counter()
            for a in component:
                for b in adjacency[a]:
                    if b in component_set and a < b:
                        relationship_count += 1
                        signal_counter.update(component_signals[frozenset((a, b))])

            sorted_ids = sorted(component)
            clusters.append(
                {
                    "cluster_id": "cluster-" + "-".join(sorted_ids),
                    "document_ids": sorted_ids,
                    "document_titles": [docs_by_id[doc_id].filename for doc_id in sorted_ids],
                    "relationship_count": relationship_count,
                    "dominant_signals": [name for name, _count in signal_counter.most_common(3)],
                }
            )

        return sorted(clusters, key=lambda c: c["cluster_id"])


document_cluster_service = DocumentClusterService()
