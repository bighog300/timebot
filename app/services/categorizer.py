import logging
import re
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.document import Document

logger = logging.getLogger(__name__)


class Categorizer:
    def apply_category(self, db: Session, document: Document, analysis: Dict[str, Any]) -> None:
        from app.config import settings

        suggested = analysis.get("suggested_category")
        confidence = float(analysis.get("category_confidence", 0.0))

        if not suggested:
            return

        if confidence < settings.CATEGORY_CONFIDENCE_THRESHOLD:
            logger.info(
                "Category confidence %.2f below threshold for %s", confidence, document.filename
            )

        category = db.query(Category).filter(Category.name.ilike(suggested)).first()
        if not category:
            category = self._create_category(db, suggested)

        document.ai_category_id = category.id
        document.ai_confidence = confidence
        db.add(document)
        db.commit()

    def _create_category(self, db: Session, name: str) -> Category:
        slug = re.sub(r"[^a-z0-9-]", "-", name.lower().replace(" ", "-").replace("&", "and"))
        slug = re.sub(r"-+", "-", slug).strip("-")

        base_slug, counter = slug, 1
        while db.query(Category).filter(Category.slug == slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1

        category = Category(name=name, slug=slug, ai_generated=True, created_by_user=False)
        db.add(category)
        db.commit()
        db.refresh(category)
        return category


categorizer = Categorizer()
