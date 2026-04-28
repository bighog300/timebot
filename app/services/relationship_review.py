from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session, aliased

from app.models.document import Document
from app.models.intelligence import DocumentRelationshipReview


class RelationshipReviewService:
    def list_items(self, db: Session, *, user_id: UUID, status: str = "pending") -> list[DocumentRelationshipReview]:
        source_doc = aliased(Document)
        target_doc = aliased(Document)
        return (
            db.query(DocumentRelationshipReview)
            .join(source_doc, source_doc.id == DocumentRelationshipReview.source_document_id)
            .join(target_doc, target_doc.id == DocumentRelationshipReview.target_document_id)
            .filter(source_doc.user_id == user_id, target_doc.user_id == user_id, DocumentRelationshipReview.status == status)
            .order_by(DocumentRelationshipReview.created_at.asc())
            .all()
        )

    def get_item(self, db: Session, *, relationship_id: UUID, user_id: UUID) -> DocumentRelationshipReview | None:
        source_doc = aliased(Document)
        target_doc = aliased(Document)
        return (
            db.query(DocumentRelationshipReview)
            .join(source_doc, source_doc.id == DocumentRelationshipReview.source_document_id)
            .join(target_doc, target_doc.id == DocumentRelationshipReview.target_document_id)
            .filter(
                source_doc.user_id == user_id,
                target_doc.user_id == user_id,
                DocumentRelationshipReview.id == relationship_id,
            )
            .first()
        )

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
        relationship_review.status = "confirmed"
        relationship_review.reviewed_at = datetime.now(timezone.utc)
        relationship_review.reviewed_by = reviewer_id
        if reason_codes_json is not None:
            relationship_review.reason_codes_json = reason_codes_json
        if metadata_json is not None:
            relationship_review.metadata_json = metadata_json
        db.add(relationship_review)
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
        relationship_review.status = "dismissed"
        relationship_review.reviewed_at = datetime.now(timezone.utc)
        relationship_review.reviewed_by = reviewer_id
        if reason_codes_json is not None:
            relationship_review.reason_codes_json = reason_codes_json
        if metadata_json is not None:
            relationship_review.metadata_json = metadata_json
        db.add(relationship_review)
        db.commit()
        db.refresh(relationship_review)
        return relationship_review


relationship_review_service = RelationshipReviewService()
