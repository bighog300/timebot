from app.models.document import Document


class SearchIndexer:
    """Helpers for composing search text used for indexing or ranking fallbacks."""

    def build_search_text(self, document: Document) -> str:
        parts = [
            document.filename or "",
            document.summary or "",
            " ".join(document.ai_tags or []),
            " ".join(document.user_tags or []),
            (document.raw_text or "")[:8000],
        ]

        if document.ai_category:
            parts.append(document.ai_category.name)
        if document.user_category:
            parts.append(document.user_category.name)

        return " ".join(p for p in parts if p).strip()


search_indexer = SearchIndexer()
