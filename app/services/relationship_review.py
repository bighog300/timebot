from datetime import datetime, timezone
import logging
from uuid import UUID

from sqlalchemy.orm import Session, aliased, contains_eager, joinedload

from app.models.document import Document
from app.models.intelligence import DocumentRelationshipReview
from app.services.review_audit import review_audit_service

logger = logging.getLogger(__name__)


class RelationshipReviewService:
    @staticmethod
    def _base_query(db: Session, *, source_doc, target_doc):
        return (
            db.query(DocumentRelationshipReview)
            .join(source_doc, source_doc.id == DocumentRelationshipReview.source_document_id)
            .join(target_doc, target_doc.id == DocumentRelationshipReview.target_document_id)
            .options(
                contains_eager(DocumentRelationshipReview.source_document, alias=source_doc).joinedload(Document.intelligence),
                contains_eager(DocumentRelationshipReview.target_document, alias=target_doc).joinedload(Document.intelligence),
            )
        )

    def list_items(self, db: Session, *, user_id: UUID, status: str = "pending") -> list[DocumentRelationshipReview]:
        source_doc = aliased(Document)
        target_doc = aliased(Document)
        items = (
            self._base_query(db, source_doc=source_doc, target_doc=target_doc)
            .filter(source_doc.user_id == user_id, target_doc.user_id == user_id, DocumentRelationshipReview.status == status)
            .order_by(DocumentRelationshipReview.created_at.asc())
            .all()
        )
        logger.info("Returning %d relationship items user_id=%s status=%s", len(items), user_id, status)
        return items

    def get_item(self, db: Session, *, relationship_id: UUID, user_id: UUID) -> DocumentRelationshipReview | None:
        source_doc = aliased(Document)
        target_doc = aliased(Document)
        return (
            self._base_query(db, source_doc=source_doc, target_doc=target_doc)
            .filter(
                source_doc.user_id == user_id,
                target_doc.user_id == user_id,
                DocumentRelationshipReview.id == relationship_id,
            )
            .first()
        )

    def list_for_document(
        self,
        db: Session,
        *,
        document_id: UUID,
        user_id: UUID,
        include_dismissed: bool = False,
        status: str | None = None,
        limit: int = 50,
    ) -> list[DocumentRelationshipReview]:
        source_doc = aliased(Document)
        target_doc = aliased(Document)
        query = (
            self._base_query(db, source_doc=source_doc, target_doc=target_doc)
            .filter(
                source_doc.user_id == user_id,
                target_doc.user_id == user_id,
                (DocumentRelationshipReview.source_document_id == document_id)
                | (DocumentRelationshipReview.target_document_id == document_id),
            )
        )
        if status:
            query = query.filter(DocumentRelationshipReview.status == status)
        elif not include_dismissed:
            query = query.filter(DocumentRelationshipReview.status.in_(("pending", "confirmed")))

        return query.order_by(
            DocumentRelationshipReview.created_at.desc(),
            DocumentRelationshipReview.id.desc(),
        ).limit(limit).all()

    def create_or_refresh_pending(
        self,
        db: Session,
        *,
        source_document_id: UUID,
        target_document_id: UUID,
        relationship_type: str,
        confidence: float | None,
        reason_codes_json: list[str] | None = None,
        metadata_json: dict | None = None,
    ) -> DocumentRelationshipReview:
        pending_matches = (
            db.query(DocumentRelationshipReview)
            .filter(
                DocumentRelationshipReview.source_document_id == source_document_id,
                DocumentRelationshipReview.target_document_id == target_document_id,
                DocumentRelationshipReview.relationship_type == relationship_type,
                DocumentRelationshipReview.status == "pending",
            )
            .order_by(DocumentRelationshipReview.created_at.asc(), DocumentRelationshipReview.id.asc())
            .all()
        )
        existing = pending_matches[0] if pending_matches else None
        if existing:
            logger.info(
                "Refreshing pending relationship review source=%s target=%s type=%s duplicates=%s",
                source_document_id,
                target_document_id,
                relationship_type,
                max(len(pending_matches) - 1, 0),
            )
            existing.confidence = confidence
            existing.reason_codes_json = reason_codes_json or []
            existing.metadata_json = metadata_json or {}
            db.add(existing)
            for duplicate in pending_matches[1:]:
                duplicate.status = "dismissed"
                duplicate.reviewed_at = datetime.now(timezone.utc)
                duplicate.metadata_json = {
                    **(duplicate.metadata_json or {}),
                    "deduplicated_to": str(existing.id),
                }
                db.add(duplicate)
            return existing

        logger.info(
            "Creating pending relationship review source=%s target=%s type=%s",
            source_document_id,
            target_document_id,
            relationship_type,
        )
        created = DocumentRelationshipReview(
            source_document_id=source_document_id,
            target_document_id=target_document_id,
            relationship_type=relationship_type,
            confidence=confidence,
            status="pending",
            reason_codes_json=reason_codes_json or [],
            metadata_json=metadata_json or {},
        )
        db.add(created)
        return created

    def confirm(
        self,
        db: Session,
        *,
        relationship_review: DocumentRelationshipReview,
        reviewer_id: UUID,
        reason_codes_json: list[str] | None = None,
        metadata_json: dict | None = None,
    ) -> DocumentRelationshipReview:
        if relationship_review.status == "confirmed":
            return relationship_review
        if relationship_review.status != "pending":
            raise ValueError("Only pending relationship reviews can be confirmed")

        before = {
            "status": relationship_review.status,
            "reviewed_at": relationship_review.reviewed_at.isoformat() if relationship_review.reviewed_at else None,
            "reviewed_by": str(relationship_review.reviewed_by) if relationship_review.reviewed_by else None,
        }
        relationship_review.status = "confirmed"
        relationship_review.reviewed_at = datetime.now(timezone.utc)
        relationship_review.reviewed_by = reviewer_id
        if reason_codes_json is not None:
            relationship_review.reason_codes_json = reason_codes_json
        if metadata_json is not None:
            relationship_review.metadata_json = metadata_json
        db.add(relationship_review)
        review_audit_service.create_event(
            db,
            document_id=relationship_review.source_document_id,
            event_type="relationship_review_confirmed",
            actor_id=reviewer_id,
            before_json=before,
            after_json={
                "status": relationship_review.status,
                "reviewed_at": relationship_review.reviewed_at.isoformat() if relationship_review.reviewed_at else None,
                "reviewed_by": str(relationship_review.reviewed_by) if relationship_review.reviewed_by else None,
                "target_document_id": str(relationship_review.target_document_id),
                "relationship_review_id": str(relationship_review.id),
            },
        )
        db.commit()
        db.refresh(relationship_review)
        return relationship_review

    def dismiss(
        self,
        db: Session,
        *,
        relationship_review: DocumentRelationshipReview,
        reviewer_id: UUID,
        reason_codes_json: list[str] | None = None,
        metadata_json: dict | None = None,
    ) -> DocumentRelationshipReview:
        if relationship_review.status == "dismissed":
            return relationship_review
        if relationship_review.status != "pending":
            raise ValueError("Only pending relationship reviews can be dismissed")

        before = {
            "status": relationship_review.status,
            "reviewed_at": relationship_review.reviewed_at.isoformat() if relationship_review.reviewed_at else None,
            "reviewed_by": str(relationship_review.reviewed_by) if relationship_review.reviewed_by else None,
        }
        relationship_review.status = "dismissed"
        relationship_review.reviewed_at = datetime.now(timezone.utc)
        relationship_review.reviewed_by = reviewer_id
        if reason_codes_json is not None:
            relationship_review.reason_codes_json = reason_codes_json
        if metadata_json is not None:
            relationship_review.metadata_json = metadata_json
        db.add(relationship_review)
        review_audit_service.create_event(
            db,
            document_id=relationship_review.source_document_id,
            event_type="relationship_review_dismissed",
            actor_id=reviewer_id,
            before_json=before,
            after_json={
                "status": relationship_review.status,
                "reviewed_at": relationship_review.reviewed_at.isoformat() if relationship_review.reviewed_at else None,
                "reviewed_by": str(relationship_review.reviewed_by) if relationship_review.reviewed_by else None,
                "target_document_id": str(relationship_review.target_document_id),
                "relationship_review_id": str(relationship_review.id),
            },
        )
        db.commit()
        db.refresh(relationship_review)
        return relationship_review


relationship_review_service = RelationshipReviewService()
