import json
import logging
import re
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.config import settings
from app.services.openai_client import openai_client_service

logger = logging.getLogger(__name__)


class CategoryDiscoveryService:
    def discover_categories(self, db: Session) -> Dict[str, Any]:
        if not openai_client_service.enabled:
            return {"error": "OPENAI_API_KEY not configured"}

        from app.models.category import Category
        from app.models.document import Document

        docs = (
            db.query(Document)
            .filter(
                Document.ai_category_id.is_(None),
                Document.processing_status == "completed",
                Document.raw_text.isnot(None),
            )
            .limit(20)
            .all()
        )

        if len(docs) < 3:
            return {"message": "Not enough uncategorized documents to discover categories", "count": len(docs)}

        sample = [
            {
                "filename": d.filename,
                "summary": (d.summary or "")[:200],
                "tags": d.ai_tags or [],
                "type": d.file_type,
            }
            for d in docs
        ]

        existing = [c.name for c in db.query(Category).all()]

        try:
            from app.prompts.category_discovery import (
                CATEGORY_DISCOVERY_SYSTEM,
                CATEGORY_DISCOVERY_TEMPLATE,
            )

            prompt = CATEGORY_DISCOVERY_TEMPLATE.format(
                documents_sample=json.dumps(sample, indent=2),
                current_categories=", ".join(existing) or "none",
            )

            response = openai_client_service.generate_completion({
                "model": settings.OPENAI_MODEL,
                "max_tokens": 2048,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": CATEGORY_DISCOVERY_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
            })

            content = (response.choices[0].message.content or "").strip()
            if content.startswith("```"):
                lines = content.splitlines()
                content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

            result = json.loads(content)
            created = self._create_categories(db, result.get("discovered_categories", []))

            return {
                "discovered": len(result.get("discovered_categories", [])),
                "created": created,
                "insights": result.get("insights", ""),
            }

        except Exception as e:
            logger.error("Category discovery error: %s", e)
            return {"error": str(e)}

    def _create_categories(self, db, categories_data) -> list:
        from app.models.category import Category

        created = []
        for cat in categories_data:
            name = cat.get("name", "").strip()
            if not name:
                continue
            if db.query(Category).filter(Category.name.ilike(name)).first():
                continue

            slug = re.sub(r"[^a-z0-9-]", "-", name.lower().replace(" ", "-"))
            slug = re.sub(r"-+", "-", slug).strip("-")
            base_slug, counter = slug, 1
            while db.query(Category).filter(Category.slug == slug).first():
                slug = f"{base_slug}-{counter}"
                counter += 1

            category = Category(
                name=name,
                slug=slug,
                description=cat.get("description"),
                color=cat.get("color", "#3B82F6"),
                icon=cat.get("icon"),
                ai_generated=True,
                created_by_user=False,
            )
            db.add(category)
            created.append(name)

        db.commit()
        return created


category_discovery = CategoryDiscoveryService()
