from __future__ import annotations

from collections import Counter
from difflib import SequenceMatcher
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.document import Document


class CategoryIntelligenceService:
    def build_intelligence(self, db: Session, user_id: Any | None = None) -> Dict[str, Any]:
        categories = db.query(Category).all()
        docs_q = db.query(Document).filter(Document.is_archived.is_(False))
        if user_id is not None:
            docs_q = docs_q.filter(Document.user_id == user_id)
        docs = docs_q.all()

        analytics = self._category_analytics(categories, docs)
        return {
            "analytics": analytics,
            "merge_recommendations": self._merge_recommendations(categories),
            "refinement_suggestions": self._refinement_suggestions(categories, docs),
        }

    def _category_analytics(self, categories: List[Category], docs: List[Document]) -> List[Dict[str, Any]]:
        totals = Counter()
        user_overrides = Counter()
        for doc in docs:
            if doc.user_category:
                totals[doc.user_category.name] += 1
                if doc.ai_category and doc.ai_category.id != doc.user_category.id:
                    user_overrides[doc.user_category.name] += 1
            elif doc.ai_category:
                totals[doc.ai_category.name] += 1
            else:
                totals["uncategorized"] += 1

        rows = []
        for category in categories:
            rows.append(
                {
                    "category_id": str(category.id),
                    "name": category.name,
                    "document_count": totals.get(category.name, 0),
                    "ai_generated": category.ai_generated,
                    "created_by_user": category.created_by_user,
                    "override_count": user_overrides.get(category.name, 0),
                }
            )
        return sorted(rows, key=lambda x: x["document_count"], reverse=True)

    def _merge_recommendations(self, categories: List[Category]) -> List[Dict[str, Any]]:
        recs = []
        for idx, left in enumerate(categories):
            for right in categories[idx + 1 :]:
                similarity = SequenceMatcher(None, left.name.lower(), right.name.lower()).ratio()
                if similarity >= 0.82:
                    recs.append(
                        {
                            "from_category_id": str(right.id),
                            "to_category_id": str(left.id),
                            "from_name": right.name,
                            "to_name": left.name,
                            "confidence": round(similarity, 4),
                            "reason": "name_similarity",
                        }
                    )
        return sorted(recs, key=lambda x: x["confidence"], reverse=True)

    def _refinement_suggestions(self, categories: List[Category], docs: List[Document]) -> List[Dict[str, Any]]:
        suggestions = []
        for category in categories:
            override_count = 0
            total = 0
            frequent_tags = Counter()
            for doc in docs:
                if doc.ai_category_id == category.id:
                    total += 1
                    if doc.user_category_id and doc.user_category_id != category.id:
                        override_count += 1
                    frequent_tags.update(doc.all_tags)

            if total == 0:
                continue

            override_ratio = override_count / total
            if override_ratio >= 0.35:
                suggestions.append(
                    {
                        "category_id": str(category.id),
                        "name": category.name,
                        "reason": "high_user_override",
                        "override_ratio": round(override_ratio, 4),
                        "top_tags": [t for t, _ in frequent_tags.most_common(5)],
                    }
                )

        return sorted(suggestions, key=lambda x: x["override_ratio"], reverse=True)


category_intelligence_service = CategoryIntelligenceService()
