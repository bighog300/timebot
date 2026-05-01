from __future__ import annotations

from pathlib import Path
import copy
import json
import logging
import time
from time import perf_counter
from typing import Any

from sqlalchemy.orm import Session, joinedload, selectinload

from app.config import settings
from app.models.document import Document
from app.models.relationships import DocumentRelationship
from app.services.document_clusters import document_cluster_service

logger = logging.getLogger(__name__)
_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}


def _cache_ttl_seconds() -> int:
    ttl = int(getattr(settings, "CHAT_RETRIEVAL_CACHE_TTL_SECONDS", 120) or 120)
    return max(60, min(300, ttl))


def _build_cache_key(*, user_id: Any, session_id: Any | None, query: str, document_ids: list[str] | None, include_timeline: bool, include_full_text: bool, max_documents: int) -> str:
    key_payload = {
        "user_id": str(user_id),
        "session_id": str(session_id) if session_id is not None else None,
        "query": query,
        "document_ids": sorted(str(i) for i in (document_ids or [])),
        "include_timeline": include_timeline,
        "include_full_text": include_full_text,
        "max_documents": max_documents,
    }
    return json.dumps(key_payload, sort_keys=True, separators=(",", ":"))


def _cache_get(cache_key: str) -> dict[str, Any] | None:
    now = time.time()
    item = _CACHE.get(cache_key)
    if not item:
        logger.info("chat_retrieval_cache", extra={"event": "chat_retrieval_cache", "cache_status": "miss"})
        return None
    expires_at, payload = item
    if now >= expires_at:
        _CACHE.pop(cache_key, None)
        logger.info("chat_retrieval_cache", extra={"event": "chat_retrieval_cache", "cache_status": "miss_expired"})
        return None
    logger.info("chat_retrieval_cache", extra={"event": "chat_retrieval_cache", "cache_status": "hit"})
    return copy.deepcopy(payload)


def _cache_set(cache_key: str, payload: dict[str, Any]) -> None:
    _CACHE[cache_key] = (time.time() + _cache_ttl_seconds(), copy.deepcopy(payload))


def _score_text(query_terms: list[str], values: list[str]) -> int:
    haystack = " ".join(v.lower() for v in values if isinstance(v, str))
    return sum(2 if term in haystack else 0 for term in query_terms)


def _excerpt_matches(query_terms: list[str], text: str, max_chars: int = 280) -> list[str]:
    if not text:
        return []
    snippets: list[str] = []
    lower = text.lower()
    for term in query_terms:
        idx = lower.find(term)
        if idx < 0:
            continue
        start = max(0, idx - 80)
        end = min(len(text), idx + max_chars)
        snippet = text[start:end].strip()
        if snippet and snippet not in snippets:
            snippets.append(snippet)
        if len(snippets) >= 3:
            break
    return snippets


def retrieve_chat_context(
    db: Session,
    query: str,
    user_id: Any,
    document_ids: list[str] | None,
    include_timeline: bool,
    include_full_text: bool,
    max_documents: int,
    session_id: Any | None = None,
) -> dict[str, Any]:

    cache_enabled = bool(getattr(settings, "CHAT_RETRIEVAL_CACHE_ENABLED", True))
    cache_key = None
    if cache_enabled:
        cache_key = _build_cache_key(
            user_id=user_id,
            session_id=session_id,
            query=query,
            document_ids=document_ids,
            include_timeline=include_timeline,
            include_full_text=include_full_text,
            max_documents=max_documents,
        )
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached

    started = perf_counter()
    query_terms = [t.strip().lower() for t in query.split() if t.strip()]
    base_q = (
        db.query(Document)
        .options(
            joinedload(Document.ai_category),
            joinedload(Document.intelligence),
            selectinload(Document.outgoing_relationships).joinedload(DocumentRelationship.target_document),
        )
        .filter(Document.user_id == user_id, Document.is_archived.is_(False))
    )
    if document_ids:
        base_q = base_q.filter(Document.id.in_(document_ids))
    candidates = base_q.all()

    full_text_by_doc: dict[str, Path] = {}
    if include_full_text:
        text_path = Path(settings.effective_artifact_dir) / "extracted_text"
        for candidate in text_path.glob("**/*.txt"):
            full_text_by_doc[candidate.stem] = candidate

    ranked: list[tuple[int, Document, dict[str, Any]]] = []
    for doc in candidates:
        title = doc.filename or str(doc.id)
        intelligence = doc.intelligence.summary if doc.intelligence and doc.intelligence.summary else ""
        category = getattr(doc.ai_category, "name", None) or ""
        timeline_events = []
        relationships = []
        matched_snippets: list[str] = []
        source_refs: list[dict[str, Any]] = []

        summary = doc.summary or intelligence or ""
        score = _score_text(query_terms, [title, summary, category])

        if summary:
            summary_snips = _excerpt_matches(query_terms, summary)
            matched_snippets.extend(summary_snips)
            if summary_snips:
                source_refs.append(
                    {"document_id": str(doc.id), "document_title": title, "kind": "summary", "quote": summary_snips[0], "page_number": None}
                )

        if include_timeline:
            events = ((doc.intelligence.entities or {}).get("timeline_events", []) if doc.intelligence and isinstance(doc.intelligence.entities, dict) else []) or ((doc.entities or {}).get("timeline_events", []) if isinstance(doc.entities, dict) else [])
            for event in events:
                if not isinstance(event, dict):
                    continue
                searchable = [event.get("title", ""), event.get("description", ""), event.get("source_quote", "")]
                ev_score = _score_text(query_terms, [str(v) for v in searchable])
                if ev_score > 0 or not query_terms:
                    timeline_events.append(event)
                    score += max(1, ev_score)
                    source_refs.append(
                        {
                            "document_id": str(doc.id),
                            "document_title": title,
                            "kind": "timeline_event",
                            "quote": event.get("source_quote") or event.get("description") or event.get("title") or "",
                            "page_number": event.get("page_number"),
                            "timeline_date": event.get("date"),
                            "timeline_start_date": event.get("start_date"),
                            "timeline_end_date": event.get("end_date"),
                        }
                    )

        for rel in doc.outgoing_relationships[:5]:
            if rel.target_document and rel.target_document.user_id == user_id:
                rel_text = f"{rel.relationship_type} {rel.target_document.filename}"
                rel_score = _score_text(query_terms, [rel_text])
                if rel_score > 0:
                    rel_metadata = rel.relationship_metadata if isinstance(rel.relationship_metadata, dict) else {}
                    relationships.append(
                        {
                            "relationship_type": rel.relationship_type,
                            "target_document_id": str(rel.target_doc_id),
                            "target_document_title": rel.target_document.filename,
                            "relationship_metadata": rel_metadata,
                        }
                    )
                    score += rel_score
                    source_refs.append({"document_id": str(doc.id), "document_title": title, "kind": "relationship", "quote": rel_text, "page_number": None})

        thread_outcome = None
        if isinstance(doc.extracted_metadata, dict):
            thread_outcome = doc.extracted_metadata.get("thread_outcome")

        if include_full_text:
            possible = full_text_by_doc.get(str(doc.id))
            if possible:
                full_text = possible.read_text(encoding="utf-8", errors="ignore")
                excerpts = _excerpt_matches(query_terms, full_text, max_chars=180)
                for ex in excerpts[:2]:
                    matched_snippets.append(ex)
                    score += 1
                    source_refs.append({"document_id": str(doc.id), "document_title": title, "kind": "full_text_excerpt", "quote": ex, "page_number": None})

        if score > 0 or (not query_terms and (summary or timeline_events)):
            ranked.append((score, doc, {"document_id": str(doc.id), "title": title, "summary": summary, "category": category, "matched_snippets": matched_snippets[:5], "timeline_events": timeline_events[:5], "relationships": relationships[:5], "email_thread_outcome": thread_outcome, "_source_refs": source_refs}))

    ranked.sort(key=lambda x: x[0], reverse=True)
    selected = ranked[: max(1, max_documents)]
    documents = [item[2] for item in selected]
    source_refs = [ref for _, _, d in selected for ref in d.pop("_source_refs", [])]

    selected_doc_ids = {d.get("document_id") for d in documents if isinstance(d, dict)}
    clusters = document_cluster_service.list_clusters_for_user(db, user_id=user_id)
    cluster_payload: list[dict[str, Any]] = []
    for cluster in clusters:
        cluster_doc_ids = cluster.get("document_ids") or []
        if not any(doc_id in selected_doc_ids for doc_id in cluster_doc_ids):
            continue
        cluster_payload.append(
            {
                "cluster_id": cluster.get("cluster_id"),
                "cluster_size": len(cluster_doc_ids),
                "document_titles": cluster.get("document_titles") or [],
                "relationship_count": cluster.get("relationship_count", 0),
                "dominant_signals": cluster.get("dominant_signals") or [],
            }
        )
        if len(cluster_payload) >= 5:
            break

    result = {"documents": documents, "source_refs": source_refs, "document_clusters": cluster_payload}
    if cache_enabled and cache_key is not None:
        _cache_set(cache_key, result)

    elapsed_ms = round((perf_counter() - started) * 1000, 2)
    logger.info("chat_retrieval_complete", extra={"event": "chat_retrieval_complete", "documents": len(documents), "source_refs": len(source_refs), "elapsed_ms": elapsed_ms})
    return result


def format_chat_context(context: dict[str, Any], max_items_per_section: int = 25) -> str:
    docs = context.get("documents") or []
    lines: list[str] = []

    lines.append("Document Summaries")
    lines.append("-")
    for d in docs[:max_items_per_section]:
        title = d.get("title") or d.get("document_id")
        summary = d.get("summary") or "(no summary)"
        category = d.get("category")
        cat_suffix = f" [Category: {category}]" if category else ""
        lines.append(f"- {title}{cat_suffix}: {summary}")
    if len(lines) == 2:
        lines.append("- None")

    lines.extend(["", "Timeline Events", "-"])
    has_timeline = False
    timeline_gaps: list[dict[str, Any]] = []
    for d in docs[:max_items_per_section]:
        title = d.get("title") or d.get("document_id")
        for event in (d.get("timeline_events") or [])[:max_items_per_section]:
            if not isinstance(event, dict):
                continue
            has_timeline = True
            date = event.get("date") or event.get("start_date") or "unknown-date"
            event_title = event.get("title") or "(untitled event)"
            description = event.get("description") or ""
            milestone_indicator = "yes" if event.get("is_milestone") else "no"
            signal_strength = event.get("signal_strength") or "unknown"
            milestone_reason = event.get("milestone_reason") or "n/a"
            lines.append(
                f"- [{date}] {title}: {event_title} — {description} "
                f"(milestone={milestone_indicator}; reason={milestone_reason}; signal_strength={signal_strength})"
            )
        for gap in (d.get("timeline_gaps") or [])[:max_items_per_section]:
            if isinstance(gap, dict):
                timeline_gaps.append(gap)
    if not has_timeline:
        lines.append("- None")
    if not timeline_gaps:
        for gap in (context.get("timeline_gaps") or [])[: max_items_per_section * 2]:
            if isinstance(gap, dict):
                timeline_gaps.append(gap)

    if timeline_gaps:
        lines.extend(["", "Timeline Gaps", "-"])
        for gap in timeline_gaps[:max_items_per_section]:
            start_date = gap.get("start_date") or "unknown-start"
            end_date = gap.get("end_date") or "unknown-end"
            duration = gap.get("gap_duration_days")
            duration_text = f"{duration} days" if duration is not None else "unknown duration"
            lines.append(f"- {start_date} -> {end_date} ({duration_text})")

    lines.extend(["", "Relationships", "-"])
    has_relationships = False
    for d in docs[:max_items_per_section]:
        source_title = d.get("title") or d.get("document_id")
        for rel in (d.get("relationships") or [])[:max_items_per_section]:
            if not isinstance(rel, dict):
                continue
            has_relationships = True
            target = rel.get("target_document_title") or rel.get("target_document_id") or "(unknown target)"
            rel_type = rel.get("relationship_type") or "related_to"
            explanation = ((rel.get("relationship_metadata") or {}).get("explanation") if isinstance(rel.get("relationship_metadata"), dict) else None)
            explanation_suffix = f" | explanation: {explanation}" if explanation else ""
            lines.append(f"- {source_title} -> {target} ({rel_type}){explanation_suffix}")
    if not has_relationships:
        lines.append("- None")

    lines.extend(["", "Document Clusters", "-"])
    has_clusters = False
    for cluster in (context.get("document_clusters") or [])[:max_items_per_section]:
        if not isinstance(cluster, dict):
            continue
        has_clusters = True
        doc_titles = [t for t in (cluster.get("document_titles") or []) if isinstance(t, str) and t.strip()]
        dominant_signals = [s for s in (cluster.get("dominant_signals") or []) if isinstance(s, str) and s.strip()]
        lines.append(f"- size={cluster.get('cluster_size')}, relationships={cluster.get('relationship_count')}")
        lines.append(f"  docs: {', '.join(doc_titles) if doc_titles else '(none)'}")
        lines.append(f"  dominant_signals: {', '.join(dominant_signals) if dominant_signals else '(none)'}")
    if not has_clusters:
        lines.append("- None")

    lines.extend(["", "Email Thread Outcomes", "-"])
    has_email_outcomes = False
    for d in docs[:max_items_per_section]:
        outcome = d.get("email_thread_outcome")
        if not isinstance(outcome, dict):
            continue
        has_email_outcomes = True
        title = d.get("title") or d.get("document_id")
        status = outcome.get("status", "unknown")
        reason = outcome.get("reason")
        confidence = outcome.get("confidence")
        meta = []
        if reason:
            meta.append(f"reason={reason}")
        if confidence is not None:
            meta.append(f"confidence={confidence}")
        suffix = f" ({', '.join(meta)})" if meta else ""
        lines.append(f"- {title}: {status}{suffix}")
    if not has_email_outcomes:
        lines.append("- None")

    lines.extend(["", "Full Text Excerpts", "-"])
    has_full_text = False
    for d in docs[:max_items_per_section]:
        title = d.get("title") or d.get("document_id")
        excerpts = d.get("matched_snippets") or []
        for excerpt in excerpts[:2]:
            has_full_text = True
            lines.append(f"- {title}: {excerpt}")
    if not has_full_text:
        lines.append("- None")

    return "\n".join(lines)
