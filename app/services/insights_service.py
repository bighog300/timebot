from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
import re
import uuid

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
    _RISK_TERMS = ("deadline", "overdue", "urgent", "risk", "issue", "blocked")

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

    def build_structured_insights(self, db: Session, *, user_id: Any) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        docs = db.query(Document).filter(Document.user_id == user_id, Document.is_archived.is_(False)).all()
        if not docs:
            return {"generated_at": now, "count": 0, "insights": []}

        insights: list[dict[str, Any]] = []
        for doc in docs:
            doc_id = str(doc.id)
            summary = ((doc.summary or "") + " " + ((getattr(doc.intelligence, "summary", None) or ""))).strip()
            timeline_events = self._timeline_events_for_doc(doc)
            for event in timeline_events:
                text = f"{event.get('title', '')} {event.get('description', '')}".lower()
                if any(term in text for term in self._RISK_TERMS):
                    insights.append(self._build_insight(
                        insight_type="risk",
                        title=f"Potential risk signal in {doc.filename}",
                        description=f"Risk wording detected in timeline event: {event.get('title', 'untitled event')}",
                        severity="medium",
                        related_document_ids=[doc_id],
                        related_event_ids=[self._event_id(doc_id, event)],
                        evidence=[self._safe_evidence(event.get("title")), self._safe_evidence(event.get("description"))],
                    ))
            if summary and any(term in summary.lower() for term in self._RISK_TERMS):
                insights.append(self._build_insight(
                    insight_type="risk",
                    title=f"Potential risk signal in {doc.filename}",
                    description="Risk wording detected in document summary.",
                    severity="medium",
                    related_document_ids=[doc_id],
                    evidence=[self._safe_evidence(summary)],
                ))
            for event in timeline_events:
                if self._is_milestone(event):
                    insights.append(self._build_insight(
                        insight_type="milestone",
                        title=event.get("title") or f"Milestone in {doc.filename}",
                        description=event.get("description") or "Milestone event extracted from timeline.",
                        severity="low",
                        related_document_ids=[doc_id],
                        related_event_ids=[self._event_id(doc_id, event)],
                        evidence=[self._safe_evidence(event.get("title"))],
                    ))
                if not event.get("date") and not event.get("start_date") and not event.get("end_date"):
                    insights.append(self._build_insight(
                        insight_type="missing_information",
                        title=f"Timeline event missing date in {doc.filename}",
                        description="A timeline event was extracted without a date.",
                        severity="low",
                        related_document_ids=[doc_id],
                        related_event_ids=[self._event_id(doc_id, event)],
                        evidence=[self._safe_evidence(event.get("title"))],
                    ))

        insights.extend(self._relationship_insights(db, docs))
        insights.extend(self._change_insights(docs))
        return {"generated_at": now, "count": len(insights), "insights": insights}

    def _relationship_insights(self, db: Session, docs: list[Document]) -> list[dict[str, Any]]:
        doc_ids = {d.id for d in docs}
        rels = db.query(DocumentRelationship).filter(
            DocumentRelationship.source_doc_id.in_(doc_ids),
            DocumentRelationship.target_doc_id.in_(doc_ids),
        ).all()
        insights: list[dict[str, Any]] = []
        pair_meta: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for rel in rels:
            meta = rel.relationship_metadata if isinstance(rel.relationship_metadata, dict) else {}
            if not meta.get("reason"):
                insights.append(self._build_insight("missing_information", "Relationship missing reason", "Relationship metadata is missing reason.", "low", [str(rel.source_doc_id), str(rel.target_doc_id)]))
            pair_key = tuple(sorted([str(rel.source_doc_id), str(rel.target_doc_id)]))
            pair_meta[pair_key].append(meta)
        for pair, metas in pair_meta.items():
            outcomes = {str(m.get("thread_outcome")).lower() for m in metas if m.get("thread_outcome")}
            if len(outcomes) > 1:
                insights.append(self._build_insight("inconsistency", "Conflicting thread outcomes detected", "Different relationship metadata indicates conflicting thread outcomes.", "high", list(pair)))
        return insights

    def _change_insights(self, docs: list[Document]) -> list[dict[str, Any]]:
        by_norm_title: dict[str, set[str]] = defaultdict(set)
        owners: dict[str, set[str]] = defaultdict(set)
        for doc in docs:
            for event in self._timeline_events_for_doc(doc):
                date = event.get("date") or event.get("start_date") or event.get("end_date")
                title = event.get("title")
                if not isinstance(title, str) or not date:
                    continue
                norm = re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()
                by_norm_title[norm].add(str(date))
                owners[norm].add(str(doc.id))
        out = []
        for norm, dates in by_norm_title.items():
            if len(dates) > 1:
                out.append(self._build_insight("change", f"Timeline progression: {norm}", "Similar milestone appears with different dates, indicating progression or schedule change.", "medium", sorted(owners.get(norm, set()))))
        return out

    def _build_insight(self, insight_type: str, title: str, description: str, severity: str, related_document_ids: list[str], related_event_ids: list[str] | None = None, evidence: list[str] | None = None) -> dict[str, Any]:
        return {"id": str(uuid.uuid4()), "type": insight_type, "title": title, "description": description, "severity": severity, "related_document_ids": related_document_ids, "related_event_ids": related_event_ids or [], "evidence": [e for e in (evidence or []) if e], "created_at": datetime.now(timezone.utc).isoformat()}

    def _timeline_events_for_doc(self, doc: Document) -> list[dict[str, Any]]:
        entities = doc.entities if isinstance(doc.entities, dict) else {}
        ie = doc.intelligence.entities if getattr(doc, "intelligence", None) and isinstance(doc.intelligence.entities, dict) else {}
        events = ie.get("timeline_events") or entities.get("timeline_events") or []
        return [e for e in events if isinstance(e, dict)]

    def _is_milestone(self, event: dict[str, Any]) -> bool:
        category = str(event.get("category", "")).lower()
        title = str(event.get("title", "")).lower()
        return category == "milestone" or "milestone" in title

    def _event_id(self, doc_id: str, event: dict[str, Any]) -> str:
        token = f"{event.get('title','')}|{event.get('date','')}|{event.get('start_date','')}|{event.get('end_date','')}"
        return f"{doc_id}:{abs(hash(token))}"

    def _safe_evidence(self, value: Any) -> str | None:
        if isinstance(value, str) and value.strip():
            return value.strip()[:240]
        return None


insights_service = InsightsService()
