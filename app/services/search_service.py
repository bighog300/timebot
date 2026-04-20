import logging
from typing import Dict, List, Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.document import Document

logger = logging.getLogger(__name__)


class SearchService:
    """Advanced full-text search with filters and ranking."""

    def search_documents(
        self,
        db: Session,
        query: str,
        filters: Optional[Dict] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Dict:
        search_query = db.query(Document).filter(Document.is_archived.is_(False))

        if query:
            ts_query = func.plainto_tsquery("english", query)
            search_query = search_query.filter(Document.search_vector.op("@@")(ts_query))

        if filters:
            search_query = self._apply_filters(search_query, filters)

        total = search_query.count()

        if query:
            search_query = search_query.order_by(
                func.ts_rank(Document.search_vector, func.plainto_tsquery("english", query)).desc(),
                Document.upload_date.desc(),
            )
        else:
            search_query = search_query.order_by(Document.upload_date.desc())

        results = search_query.offset(skip).limit(limit).all()

        results_with_scores = []
        for document in results:
            results_with_scores.append(
                {
                    "document": document,
                    "relevance": self._calculate_relevance(document, query),
                    "highlights": self._generate_highlights(document, query),
                }
            )

        return {
            "results": results_with_scores,
            "total": total,
            "query": query,
            "filters": filters,
            "page": (skip // limit) + 1,
            "pages": (total + limit - 1) // limit if total else 0,
        }

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
                query = query.filter(
                    or_(
                        Document.ai_tags.contains([tag]),
                        Document.user_tags.contains([tag]),
                    )
                )

        if filters.get("is_favorite") is not None:
            query = query.filter(Document.is_favorite == filters["is_favorite"])

        if filters.get("file_types"):
            query = query.filter(Document.file_type.in_(filters["file_types"]))

        return query

    def _calculate_relevance(self, document: Document, query: str) -> float:
        if not query:
            return 1.0

        query_lower = query.lower()
        score = 0.0

        if query_lower in (document.filename or "").lower():
            score += 0.3
        if document.summary and query_lower in document.summary.lower():
            score += 0.25

        all_tags = (document.ai_tags or []) + (document.user_tags or [])
        if any(query_lower in tag.lower() for tag in all_tags):
            score += 0.2

        if document.ai_category and query_lower in document.ai_category.name.lower():
            score += 0.15

        if document.entities:
            for _, entities in document.entities.items():
                if any(query_lower in str(entity).lower() for entity in entities):
                    score += 0.1
                    break

        return min(score, 1.0)

    def _generate_highlights(self, document: Document, query: str) -> List[str]:
        if not query:
            return []

        highlights: List[str] = []
        query_lower = query.lower()

        if document.summary and query_lower in document.summary.lower():
            idx = document.summary.lower().find(query_lower)
            start = max(0, idx - 50)
            end = min(len(document.summary), idx + len(query) + 50)
            snippet = document.summary[start:end]
            if start > 0:
                snippet = "..." + snippet
            if end < len(document.summary):
                snippet += "..."
            highlights.append(snippet)

        if document.raw_text and query_lower in document.raw_text.lower():
            idx = document.raw_text.lower().find(query_lower)
            start = max(0, idx - 100)
            end = min(len(document.raw_text), idx + len(query) + 100)
            snippet = document.raw_text[start:end]
            if start > 0:
                snippet = "..." + snippet
            if end < len(document.raw_text):
                snippet += "..."
            highlights.append(snippet)

        return highlights[:3]

    def get_search_suggestions(self, db: Session, partial_query: str, limit: int = 5) -> List[str]:
        suggestions = set()

        categories = (
            db.query(Category)
            .filter(Category.name.ilike(f"%{partial_query}%"))
            .limit(limit)
            .all()
        )
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
