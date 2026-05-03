import uuid

from app.models.relationships import DocumentRelationship


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
        workspace_id=sample_document.workspace_id if user_id == sample_document.user_id else None,
    )
    db.add(doc)
    db.flush()
    return doc


def test_document_clusters_group_related_documents(client, db, sample_document, test_user):
    related = _make_doc(db, sample_document, filename="related.pdf", user_id=test_user.id)
    db.add(
        DocumentRelationship(
            source_doc_id=sample_document.id,
            target_doc_id=related.id,
            relationship_type="related_to",
            confidence=0.8,
            relationship_metadata={"explanation": {"signals": ["ai_detected"], "reason": "semantic overlap"}},
        )
    )
    db.commit()

    resp = client.get("/api/v1/documents/clusters")
    assert resp.status_code == 200
    clusters = resp.json()
    combined = next(row for row in clusters if len(row["document_ids"]) == 2)
    assert str(sample_document.id) in combined["document_ids"]
    assert str(related.id) in combined["document_ids"]
    assert combined["relationship_count"] == 1


def test_document_clusters_keep_unrelated_documents_separate(client, db, sample_document, test_user):
    unrelated = _make_doc(db, sample_document, filename="unrelated.pdf", user_id=test_user.id)
    db.commit()

    resp = client.get("/api/v1/documents/clusters")
    assert resp.status_code == 200
    clusters = resp.json()
    assert any(row["document_ids"] == [str(sample_document.id)] for row in clusters)
    assert any(row["document_ids"] == [str(unrelated.id)] for row in clusters)


def test_document_clusters_do_not_mix_users(client, db, sample_document, test_user):
    other_doc = _make_doc(db, sample_document, filename="other-user.pdf", user_id=uuid.uuid4())
    db.add(
        DocumentRelationship(
            source_doc_id=sample_document.id,
            target_doc_id=other_doc.id,
            relationship_type="related_to",
            confidence=0.5,
        )
    )
    db.commit()

    resp = client.get("/api/v1/documents/clusters")
    assert resp.status_code == 200
    clusters = resp.json()
    assert len(clusters) == 1
    assert clusters[0]["document_ids"] == [str(sample_document.id)]


def test_document_clusters_include_dominant_signals(client, db, sample_document, test_user):
    doc_b = _make_doc(db, sample_document, filename="doc-b.pdf", user_id=test_user.id)
    doc_c = _make_doc(db, sample_document, filename="doc-c.pdf", user_id=test_user.id)
    db.add_all([
        DocumentRelationship(
            source_doc_id=sample_document.id,
            target_doc_id=doc_b.id,
            relationship_type="thread",
            confidence=0.99,
            relationship_metadata={"explanation": {"signals": ["structural_email_thread", "ai_detected"]}},
        ),
        DocumentRelationship(
            source_doc_id=doc_b.id,
            target_doc_id=doc_c.id,
            relationship_type="related_to",
            confidence=0.9,
            relationship_metadata={"explanation": {"signals": ["ai_detected"]}},
        ),
    ])
    db.commit()

    resp = client.get("/api/v1/documents/clusters")
    assert resp.status_code == 200
    clusters = resp.json()
    combined = next(row for row in clusters if len(row["document_ids"]) == 3)
    assert combined["dominant_signals"][0] == "ai_detected"
