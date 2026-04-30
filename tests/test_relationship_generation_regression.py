import uuid
from unittest.mock import patch

from app.models.document import Document
from app.models.intelligence import DocumentIntelligence, DocumentRelationshipReview
from app.services.document_processor import document_processor


def _make_doc(db, user_id, filename: str) -> Document:
    doc = Document(
        id=uuid.uuid4(),
        filename=filename,
        original_path=f"/tmp/{filename}",
        file_type="pdf",
        file_size=1024,
        mime_type="application/pdf",
        processing_status="queued",
        is_archived=False,
        source="upload",
        user_id=user_id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def test_processing_creates_intelligence_and_pending_relationship_without_duplicates(db, test_user):
    existing = _make_doc(db, test_user.id, "project-alpha-plan.pdf")
    existing.summary = "Roadmap for Project Alpha launch milestones."
    existing.ai_tags = ["project-alpha", "roadmap", "launch"]
    existing.entities = {"projects": ["Project Alpha"], "teams": ["Ops"]}
    existing.processing_status = "completed"
    db.add(existing)
    db.commit()

    incoming = _make_doc(db, test_user.id, "project-alpha-plan.pdf")

    analysis = {
        "summary": "Roadmap for Project Alpha launch milestones.",
        "key_points": ["Launch timeline", "Milestone updates"],
        "tags": ["project-alpha", "launch", "status"],
        "entities": {"projects": ["Project Alpha"], "teams": ["Ops"]},
        "action_items": [],
        "model_version": "test-model",
        "model_metadata": {"provider": "test"},
    }

    with patch("app.services.text_extractor.text_extractor.extract", return_value=("alpha content", 1, 10)), patch(
        "app.services.thumbnail_generator.thumbnail_generator.generate", return_value=None
    ), patch("app.services.ai_analyzer.ai_analyzer.analyze_document", return_value=analysis), patch(
        "app.services.ai_analyzer.ai_analyzer.compute_confidence", return_value=0.9
    ):
        document_processor.process_document(db, incoming)
        document_processor.process_document(db, incoming)

    intelligence = db.query(DocumentIntelligence).filter(DocumentIntelligence.document_id == incoming.id).first()
    assert intelligence is not None

    pending_reviews = (
        db.query(DocumentRelationshipReview)
        .filter(
            DocumentRelationshipReview.source_document_id == min(existing.id, incoming.id, key=str),
            DocumentRelationshipReview.target_document_id == max(existing.id, incoming.id, key=str),
            DocumentRelationshipReview.status == "pending",
        )
        .all()
    )
    assert len(pending_reviews) == 1
