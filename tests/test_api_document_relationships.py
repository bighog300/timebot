import uuid

from app.models.intelligence import DocumentIntelligence, DocumentRelationshipReview


def _make_doc(db, sample_document, *, filename: str, user_id):
    doc = type(sample_document)(
        id=uuid.uuid4(),
        filename=filename,
        original_path=f"/tmp/{filename}",
        file_type="pdf",
        file_size=100,
        mime_type="application/pdf",
        processing_status="completed",
        source="upload",
        user_id=user_id,
    )
    db.add(doc)
    db.flush()
    return doc


def test_document_relationships_include_source_and_target(client, db, sample_document, test_user):
    source_related = _make_doc(db, sample_document, filename="source-related.pdf", user_id=test_user.id)
    target_related = _make_doc(db, sample_document, filename="target-related.pdf", user_id=test_user.id)
    db.add(DocumentIntelligence(document_id=source_related.id, summary="source intelligence"))
    sample_document.raw_text = "sample raw text for source fallback"
    db.add_all([
        DocumentRelationshipReview(
            source_document_id=sample_document.id,
            target_document_id=source_related.id,
            relationship_type="related",
            status="confirmed",
            confidence=0.9,
            metadata_json={"explanation": {"signals": ["ai_detected", "shared_terms"], "reason": "AI detected shared terms."}},
        ),
        DocumentRelationshipReview(
            source_document_id=target_related.id,
            target_document_id=sample_document.id,
            relationship_type="similar",
            status="pending",
            confidence=0.7,
        ),
    ])
    db.commit()

    resp = client.get(f"/api/v1/documents/{sample_document.id}/relationships")
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 2
    ids = {row["related_document_id"] for row in rows}
    assert str(source_related.id) in ids
    assert str(target_related.id) in ids
    source_row = next(row for row in rows if row["related_document_id"] == str(source_related.id))
    assert source_row["direction"] == "source"
    assert source_row["related_document_title"] == "source-related.pdf"
    assert source_row["related_document_snippet"] == "source intelligence"
    assert source_row["explanation_metadata"]["signals"] == ["ai_detected", "shared_terms"]


def test_document_relationships_excludes_dismissed_by_default(client, db, sample_document, test_user):
    related = _make_doc(db, sample_document, filename="dismissed.pdf", user_id=test_user.id)
    db.add(DocumentRelationshipReview(
        source_document_id=sample_document.id,
        target_document_id=related.id,
        relationship_type="related",
        status="dismissed",
    ))
    db.commit()

    hidden = client.get(f"/api/v1/documents/{sample_document.id}/relationships")
    assert hidden.status_code == 200
    assert hidden.json() == []

    shown = client.get(f"/api/v1/documents/{sample_document.id}/relationships?include_dismissed=true")
    assert shown.status_code == 200
    assert len(shown.json()) == 1


def test_document_relationships_enforces_permissions(client, db, sample_document, test_user):
    other_user_id = uuid.uuid4()
    unrelated = _make_doc(db, sample_document, filename="other-user.pdf", user_id=other_user_id)
    db.add(DocumentRelationshipReview(
        source_document_id=sample_document.id,
        target_document_id=unrelated.id,
        relationship_type="related",
        status="pending",
    ))
    db.commit()

    resp = client.get(f"/api/v1/documents/{sample_document.id}/relationships")
    assert resp.status_code == 200
    assert resp.json() == []
