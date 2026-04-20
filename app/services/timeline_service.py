from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from sqlalchemy.orm import Session
except ModuleNotFoundError:  # pragma: no cover - local test fallback when deps are unavailable
    Session = Any

try:
    from app.models.document import Document
except ModuleNotFoundError:  # pragma: no cover - local test fallback when deps are unavailable
    class _ModelFieldFallback:
        def is_(self, *_args, **_kwargs):
            return self

        def in_(self, *_args, **_kwargs):
            return self

        def desc(self):
            return self

        def __or__(self, _other):
            return self

    class Document:  # type: ignore[no-redef]
        is_archived = _ModelFieldFallback()
        ai_category_id = _ModelFieldFallback()
        user_category_id = _ModelFieldFallback()
        source = _ModelFieldFallback()
        file_type = _ModelFieldFallback()
        upload_date = _ModelFieldFallback()


class TimelineService:
    def build_timeline(
        self,
        db: Session,
        *,
        group_by: str = "day",
        category_ids: Optional[List[str]] = None,
        sources: Optional[List[str]] = None,
        file_types: Optional[List[str]] = None,
        limit: int = 500,
    ) -> Dict[str, Any]:
        query = db.query(Document).filter(Document.is_archived.is_(False))

        if category_ids:
            query = query.filter(
                (Document.ai_category_id.in_(category_ids)) | (Document.user_category_id.in_(category_ids))
            )
        if sources:
            query = query.filter(Document.source.in_(sources))
        if file_types:
            query = query.filter(Document.file_type.in_(file_types))

        docs = query.order_by(Document.upload_date.desc()).limit(limit).all()

        grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for doc in docs:
            for event in self._events_for_document(doc):
                key = self._group_key(event["date"], group_by)
                grouped[key].append(event)

        buckets = [
            {"period": period, "count": len(events), "events": sorted(events, key=lambda e: e["date"], reverse=True)}
            for period, events in sorted(grouped.items(), reverse=True)
        ]

        return {
            "group_by": group_by,
            "total_documents": len(docs),
            "total_events": sum(b["count"] for b in buckets),
            "buckets": buckets,
        }

    def _events_for_document(self, doc: Document) -> List[Dict[str, Any]]:
        events: List[Dict[str, Any]] = []
        upload = doc.upload_date
        if upload:
            events.append(
                {
                    "type": "upload",
                    "date": upload,
                    "document_id": str(doc.id),
                    "filename": doc.filename,
                    "source": doc.source,
                    "file_type": doc.file_type,
                }
            )

        extracted_dates = []
        entities = doc.entities or {}
        if isinstance(entities, dict):
            extracted_dates = entities.get("dates", []) or entities.get("DATE", []) or []

        for value in extracted_dates:
            parsed = self._parse_date(value)
            if not parsed:
                continue
            events.append(
                {
                    "type": "entity_date",
                    "date": parsed,
                    "document_id": str(doc.id),
                    "filename": doc.filename,
                    "source": doc.source,
                    "file_type": doc.file_type,
                    "raw_value": value,
                }
            )

        return events or [
            {
                "type": "upload_fallback",
                "date": upload,
                "document_id": str(doc.id),
                "filename": doc.filename,
                "source": doc.source,
                "file_type": doc.file_type,
            }
        ]

    def _group_key(self, dt: datetime, group_by: str) -> str:
        if group_by == "month":
            return dt.strftime("%Y-%m")
        if group_by == "week":
            year, week, _ = dt.isocalendar()
            return f"{year}-W{week:02d}"
        return dt.strftime("%Y-%m-%d")

    def _parse_date(self, value: Any) -> Optional[datetime]:
        if isinstance(value, datetime):
            return value
        if not isinstance(value, str):
            return None

        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(value.strip(), fmt)
            except Exception:
                continue
        return None


timeline_service = TimelineService()
