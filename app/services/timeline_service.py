from __future__ import annotations

from datetime import datetime
import logging
import re
from typing import Any, Dict, List, Optional

try:
    from sqlalchemy.orm import Session
except ModuleNotFoundError:  # pragma: no cover
    Session = Any

try:
    from app.models.document import Document
except ModuleNotFoundError:  # pragma: no cover
    class _ModelFieldFallback:
        def is_(self, *_args, **_kwargs): return self
        def in_(self, *_args, **_kwargs): return self
        def desc(self): return self
    class Document:  # type: ignore[no-redef]
        is_archived=_ModelFieldFallback(); ai_category_id=_ModelFieldFallback(); user_category_id=_ModelFieldFallback(); source=_ModelFieldFallback(); file_type=_ModelFieldFallback(); upload_date=_ModelFieldFallback(); id=_ModelFieldFallback()

class TimelineService:
    def build_timeline(self, db: Session, *, group_by: str = "day", category_ids: Optional[List[str]] = None, sources: Optional[List[str]] = None, file_types: Optional[List[str]] = None, document_id: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None, category: Optional[str] = None, min_confidence: float = 0.0, limit: int = 500) -> Dict[str, Any]:
        query = db.query(Document).filter(Document.is_archived.is_(False))
        if category_ids:
            query = query.filter((Document.ai_category_id.in_(category_ids)) | (Document.user_category_id.in_(category_ids)))
        if sources:
            query = query.filter(Document.source.in_(sources))
        if file_types:
            query = query.filter(Document.file_type.in_(file_types))
        if document_id:
            query = query.filter(Document.id == document_id)

        docs = query.order_by(Document.upload_date.desc()).limit(limit).all()
        events: List[Dict[str, Any]] = []
        for doc in docs:
            events.extend(self._events_for_document(doc))
        logging.getLogger(__name__).info("timeline_service_scan docs=%s events_before_filter=%s", len(docs), len(events))

        sd = self._parse_date(start_date) if start_date else None
        ed = self._parse_date(end_date) if end_date else None
        filtered=[]
        for ev in events:
            conf=float(ev.get('confidence') or 0.0)
            if conf < min_confidence: continue
            if category and ev.get('category') != category: continue
            d = self._parse_date(ev.get('date')) or self._parse_date(ev.get('start_date'))
            if sd and d and d < sd: continue
            if ed and d and d > ed: continue
            filtered.append(ev)
        filtered.sort(key=lambda e: e.get("start_date") or e.get("date") or "", reverse=False)
        buckets = [{"period": "all", "count": len(filtered), "events": filtered}]
        logging.getLogger(__name__).info("timeline_service_result docs=%s events_returned=%s", len(docs), len(filtered))
        return {"group_by": group_by, "total_documents": len(docs), "total_events": len(filtered), "events": filtered, "buckets": buckets}

    def _events_for_document(self, doc: Document) -> List[Dict[str, Any]]:
        entities = doc.entities or {}
        intelligence_entities = ((getattr(doc, "intelligence", None) or {}).get("entities") if isinstance(getattr(doc, "intelligence", None), dict) else None) or {}
        raw_events = []
        if isinstance(intelligence_entities, dict):
            raw_events = intelligence_entities.get('timeline_events', []) or []
        if not raw_events and isinstance(entities, dict):
            raw_events = entities.get('timeline_events', []) or []
        if not raw_events:
            raw_events = self._fallback_extract_from_text(getattr(doc, "raw_text", "") or "")
        normalized=[]
        for event in raw_events:
            if not isinstance(event, dict):
                continue
            normalized.append({
                'title': event.get('title') or 'Untitled event',
                'description': event.get('description'),
                'date': event.get('date'),
                'start_date': event.get('start_date'),
                'end_date': event.get('end_date'),
                'confidence': float(event.get('confidence') or 0.0),
                'source_quote': event.get('source_quote'),
                'page_number': event.get('page_number'),
                'document_id': str(doc.id),
                'document_title': doc.filename,
                'category': event.get('category'),
                'source': event.get('source', 'extracted'),
            })
        return normalized

    def _fallback_extract_from_text(self, text: str) -> List[Dict[str, Any]]:
        if not text:
            return []
        events = []
        patterns = [r"\b\d{4}-\d{2}-\d{2}\b", r"\b[A-Z][a-z]+ \d{1,2}, \d{4}\b", r"\b\d{1,2}/\d{1,2}/\d{4}\b"]
        for sentence in re.split(r"(?<=[.!?])\s+", text):
            for p in patterns:
                for m in re.finditer(p, sentence):
                    d = self._parse_date(m.group(0))
                    if not d:
                        continue
                    events.append({
                        "title": sentence[:60].strip() or "Dated event",
                        "description": None,
                        "date": d.date().isoformat(),
                        "start_date": None,
                        "end_date": None,
                        "confidence": 0.25,
                        "source_quote": sentence[:220],
                        "page_number": None,
                        "category": "fallback_date",
                        "source": "date_extraction_fallback",
                    })
        return events

    def _parse_date(self, value: Any) -> Optional[datetime]:
        if isinstance(value, datetime):
            return value
        if not isinstance(value, str) or not value.strip():
            return None
        s=value.strip().replace('Z','+00:00')
        try:
            return datetime.fromisoformat(s)
        except Exception:
            for fmt in ("%B %d, %Y", "%d %B %Y", "%m/%d/%Y", "%d/%m/%Y"):
                try:
                    return datetime.strptime(s, fmt)
                except ValueError:
                    continue
            return None

timeline_service = TimelineService()
