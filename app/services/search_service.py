import logging
import re
from collections import defaultdict
from typing import Any, Dict, List, Optional

from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.document import Document
from app.services.embedding_service import embedding_service
from app.services.query_parser import ParsedQuery, query_parser

logger = logging.getLogger(__name__)


class SearchService:
    """Advanced full-text, semantic, and hybrid search services."""

    def search_documents(
        self,
        db: Session,
        query: str,
        filters: Optional[Dict] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Dict[str, Any]:
        parsed = query_parser.parse(query)
        search_query = db.query(Document).filter(Document.is_archived.is_(False))

        if parsed.normalized:
            ts_query = self._build_ts_query(parsed)
            if ts_query:
                search_query = search_query.filter(Document.search_vector.op("@@")(ts_query))

        if filters:
            search_query = self._apply_filters(search_query, filters)

        total = search_query.count()

        if parsed.normalized:
            ts_query = self._build_ts_query(parsed)
            search_query = search_query.order_by(
                func.ts_rank_cd(Document.search_vector, ts_query).desc(),
                Document.upload_date.desc(),
            )
        else:
            search_query = search_query.order_by(Document.upload_date.desc())

        results = search_query.offset(skip).limit(limit).all()

        items = []
        for document in results:
            relevance, breakdown = self._calculate_relevance(document, parsed)
            items.append(
                {
                    "document": document,
                    "relevance": relevance,
                    "score_breakdown": breakdown,
                    "highlights": self._generate_highlights(document, parsed),
                }
            )

        return {
            "results": items,
            "total": total,
            "query": query,
            "parsed_query": parsed.as_debug(),
            "filters": filters,
            "page": (skip // limit) + 1,
            "pages": (total + limit - 1) // limit if total else 0,
        }

    def hybrid_search_documents(
        self,
        db: Session,
        query: str,
        filters: Optional[Dict] = None,
        skip: int = 0,
        limit: int = 20,
        lexical_weight: float = 0.6,
        semantic_weight: float = 0.4,
        semantic_threshold: float = 0.35,
    ) -> Dict[str, Any]:
        lexical = self.search_documents(db=db, query=query, filters=filters, skip=0, limit=max(limit * 3, 20))
        lexical_docs = lexical["results"]

        semantic_available = embedding_service.enabled
        semantic_matches: List[Dict[str, Any]] = []
        if semantic_available:
            semantic_matches = embedding_service.semantic_search(
                query=query,
                limit=max(limit * 3, 20),
                score_threshold=semantic_threshold,
            )

        semantic_scores = {item["document_id"]: item for item in semantic_matches}

        all_ids = list({str(i["document"].id) for i in lexical_docs} | set(semantic_scores.keys()))
        docs = db.query(Document).filter(Document.id.in_(all_ids)).all() if all_ids else []
        by_id = {str(doc.id): doc for doc in docs}

        merged: List[Dict[str, Any]] = []
        lexical_ranked = {str(item["document"].id): item for item in lexical_docs}

        max_lex = max((item["relevance"] for item in lexical_docs), default=1.0)
        max_sem = max((item["score"] for item in semantic_matches), default=1.0)

        for doc_id in all_ids:
            doc = by_id.get(doc_id)
            if not doc:
                continue

            lex_item = lexical_ranked.get(doc_id)
            sem_item = semantic_scores.get(doc_id)

            lex_score = (lex_item["relevance"] / max_lex) if lex_item else 0.0
            sem_score = (sem_item["score"] / max_sem) if sem_item else 0.0
            combined = (lex_score * lexical_weight) + (sem_score * semantic_weight)

            merged.append(
                {
                    "document": doc,
                    "relevance": combined,
                    "score_breakdown": {
                        "combined": round(combined, 5),
                        "lexical": round(lex_score, 5),
                        "semantic": round(sem_score, 5),
                        "weights": {"lexical": lexical_weight, "semantic": semantic_weight},
                        "semantic_available": semantic_available,
                    },
                    "highlights": lex_item["highlights"] if lex_item else self._generate_highlights(doc, query_parser.parse(query)),
                }
            )

        merged.sort(key=lambda x: (x["relevance"], x["document"].upload_date), reverse=True)
        paged = merged[skip : skip + limit]

        return {
            "results": paged,
            "total": len(merged),
            "query": query,
            "filters": filters,
            "page": (skip // limit) + 1,
            "pages": (len(merged) + limit - 1) // limit if merged else 0,
            "degraded": not semantic_available,
            "debug": {
                "lexical_hits": len(lexical_docs),
                "semantic_hits": len(semantic_matches),
                "semantic_threshold": semantic_threshold,
            },
        }

    def _build_ts_query(self, parsed: ParsedQuery):
        if parsed.phrases:
            raw_query = " & ".join([f"({p.replace(' ', ' <-> ')})" for p in parsed.phrases + parsed.terms])
            return func.to_tsquery("english", raw_query)
        if parsed.terms:
            return func.plainto_tsquery("english", " ".join(parsed.terms))
        return None

    def _apply_filters(self, query, filters: Dict):
        if filters.get("categories"):
            query = query.filter(
                or_(
                    Document.ai_category_id.in_(filters["categories"]),
                    Document.user_category_id.in_(filters["categories"]),
                )
            )

        if filters.get("sources"):
            query = query.filter(Document.source.in_(filters["sources"]))

        if filters.get("date_range"):
            if filters["date_range"].get("start"):
                query = query.filter(Document.upload_date >= filters["date_range"]["start"])
            if filters["date_range"].get("end"):
                query = query.filter(Document.upload_date <= filters["date_range"]["end"])

        if filters.get("tags"):
            for tag in filters["tags"]:
                query = query.filter(or_(Document.ai_tags.contains([tag]), Document.user_tags.contains([tag])))

        if filters.get("is_favorite") is not None:
            query = query.filter(Document.is_favorite == filters["is_favorite"])

        if filters.get("file_types"):
            query = query.filter(Document.file_type.in_(filters["file_types"]))

        return query

    def _calculate_relevance(self, document: Document, parsed: ParsedQuery) -> tuple[float, Dict[str, float]]:
        if not parsed.normalized:
            return 1.0, {"base": 1.0}

        haystacks = {
            "filename": (document.filename or "").lower(),
            "summary": (document.summary or "").lower(),
            "tags": " ".join((document.ai_tags or []) + (document.user_tags or [])).lower(),
            "category": " ".join(
                [
                    document.ai_category.name if document.ai_category else "",
                    document.user_category.name if document.user_category else "",
                ]
            ).lower(),
            "entities": str(document.entities or {}).lower(),
        }

        weights = {"filename": 0.35, "summary": 0.25, "tags": 0.2, "category": 0.1, "entities": 0.1}
        breakdown: Dict[str, float] = defaultdict(float)

        for term in parsed.terms + parsed.phrases:
            for field, weight in weights.items():
                if term in haystacks[field]:
                    breakdown[field] += weight / max(len(parsed.terms + parsed.phrases), 1)

        penalty = 0.0
        for excluded in parsed.excluded_terms:
            if any(excluded in text for text in haystacks.values()):
                penalty += 0.15

        score = max(0.0, min(1.0, sum(breakdown.values()) - penalty))
        breakdown["penalty"] = round(penalty, 5)
        return round(score, 5), {k: round(v, 5) for k, v in breakdown.items()}

    def _generate_highlights(self, document: Document, parsed: ParsedQuery) -> List[str]:
        if not parsed.normalized:
            return []

        targets = parsed.phrases + parsed.terms
        if not targets:
            return []

        source_text = (document.summary or "") + "\n" + (document.raw_text or "")
        if not source_text.strip():
            return []

        snippets: List[str] = []
        lowered = source_text.lower()

        for token in targets[:3]:
            idx = lowered.find(token)
            if idx < 0:
                continue
            start = max(0, idx - 70)
            end = min(len(source_text), idx + len(token) + 70)
            snippet = source_text[start:end].strip()
            if start > 0:
                snippet = "..." + snippet
            if end < len(source_text):
                snippet = snippet + "..."
            snippets.append(self._emphasize(snippet, token))

        return snippets[:3]

    @staticmethod
    def _emphasize(text: str, token: str) -> str:
        try:
            return re.sub(
                re.escape(token),
                lambda m: f"**{m.group(0)}**",
                text,
                flags=re.IGNORECASE,
            )
        except Exception:
            return text

    def get_search_suggestions(self, db: Session, partial_query: str, limit: int = 5) -> List[str]:
        suggestions = set()

        categories = db.query(Category).filter(Category.name.ilike(f"%{partial_query}%")).limit(limit).all()
        for category in categories:
            suggestions.add(category.name)

        docs_with_tags = (
            db.query(Document.ai_tags, Document.user_tags)
            .filter(
                or_(
                    func.array_to_string(Document.ai_tags, " ").ilike(f"%{partial_query}%"),
                    func.array_to_string(Document.user_tags, " ").ilike(f"%{partial_query}%"),
                )
            )
            .limit(limit * 2)
            .all()
        )

        for ai_tags, user_tags in docs_with_tags:
            for tag in (ai_tags or []) + (user_tags or []):
                if partial_query.lower() in tag.lower():
                    suggestions.add(tag)

        filename_hits = (
            db.query(Document.filename)
            .filter(Document.filename.ilike(f"%{partial_query}%"))
            .order_by(case((Document.is_favorite.is_(True), 0), else_=1), Document.upload_date.desc())
            .limit(limit)
            .all()
        )
        for (filename,) in filename_hits:
            suggestions.add(filename)

        return sorted(suggestions)[:limit]

    def get_popular_searches(self, db: Session, limit: int = 10) -> List[Dict]:
        popular_categories = (
            db.query(Category.name, Category.document_count)
            .filter(Category.document_count > 0)
            .order_by(Category.document_count.desc())
            .limit(limit)
            .all()
        )

        return [{"term": name, "count": count} for name, count in popular_categories]


search_service = SearchService()
