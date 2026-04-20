from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

try:
    from sqlalchemy.orm import Session
except ModuleNotFoundError:  # pragma: no cover - local test fallback when deps are unavailable
    Session = Any

try:
    from app.models.document import Document
    from app.models.relationships import DocumentRelationship
except ModuleNotFoundError:  # pragma: no cover - local test fallback when deps are unavailable
    class _ModelFieldFallback:
        def is_(self, *_args, **_kwargs):
            return self

        def __eq__(self, _other):
            return self

    class Document:  # type: ignore[no-redef]
        is_archived = _ModelFieldFallback()

    class DocumentRelationship:  # type: ignore[no-redef]
        relationship_type = _ModelFieldFallback()


class InsightsService:
    def build_dashboard(self, db: Session, lookback_days: int = 30) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        since = now - timedelta(days=lookback_days)

        docs = db.query(Document).filter(Document.is_archived.is_(False)).all()
        recent_docs = [d for d in docs if d.upload_date and d.upload_date >= since]

        return {
            "generated_at": now.isoformat(),
            "lookback_days": lookback_days,
            "volume_trends": self._volume_trends(recent_docs),
            "category_distribution": self._category_distribution(db, docs),
            "source_distribution": dict(Counter(d.source for d in docs)),
            "action_item_summary": self._action_item_summary(docs),
            "duplicate_clusters": self._duplicate_clusters(db),
            "relationship_summary": self._relationship_summary(db),
            "recent_activity": self._recent_activity(recent_docs),
        }

    def _volume_trends(self, docs: List[Document]) -> List[Dict[str, Any]]:
        buckets = defaultdict(int)
        for doc in docs:
            buckets[doc.upload_date.strftime("%Y-%m-%d")] += 1
        return [{"date": day, "count": buckets[day]} for day in sorted(buckets)]

    def _category_distribution(self, db: Session, docs: List[Document]) -> List[Dict[str, Any]]:
        counts = Counter()
        for doc in docs:
            if doc.user_category:
                counts[doc.user_category.name] += 1
            elif doc.ai_category:
                counts[doc.ai_category.name] += 1
            else:
                counts["uncategorized"] += 1

        return [{"name": name, "count": count} for name, count in counts.most_common()]

    def _action_item_summary(self, docs: List[Document]) -> Dict[str, Any]:
        total = 0
        pending = 0
        for doc in docs:
            for item in doc.action_items or []:
                total += 1
                text = str(item).lower()
                if "todo" in text or "pending" in text or "follow up" in text:
                    pending += 1
        return {"total": total, "pending_estimate": pending}

    def _duplicate_clusters(self, db: Session) -> List[List[str]]:
        rels = db.query(DocumentRelationship).filter(DocumentRelationship.relationship_type == "duplicates").all()
        if not rels:
            return []
        clusters: Dict[str, set] = {}
        for rel in rels:
            a = str(rel.source_doc_id)
            b = str(rel.target_doc_id)
            key = min(a, b)
            clusters.setdefault(key, set()).update([a, b])
        return [sorted(list(v)) for v in clusters.values()]

    def _relationship_summary(self, db: Session) -> Dict[str, int]:
        rels = db.query(DocumentRelationship.relationship_type).all()
        return dict(Counter(r[0] for r in rels))

    def _recent_activity(self, docs: List[Document]) -> List[Dict[str, Any]]:
        sorted_docs = sorted(docs, key=lambda d: d.upload_date, reverse=True)[:20]
        return [
            {
                "document_id": str(doc.id),
                "filename": doc.filename,
                "upload_date": doc.upload_date.isoformat(),
                "source": doc.source,
                "status": doc.processing_status,
            }
            for doc in sorted_docs
        ]


insights_service = InsightsService()
