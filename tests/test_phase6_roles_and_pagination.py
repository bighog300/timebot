import uuid

from fastapi.testclient import TestClient

from app.api.deps import get_current_user, get_db
from app.main import app
from app.models.intelligence import DocumentActionItem, DocumentRelationshipReview, DocumentReviewItem


def _client_for_user(db, user):
    def override_get_db():
        yield db

    def override_get_current_user():
        return user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    return TestClient(app)


def _seed_relationship_review(db, sample_document):
    target = type(sample_document)(
        id=uuid.uuid4(),
        filename='target-role.pdf',
        original_path='/tmp/target-role.pdf',
        file_type='pdf',
        file_size=100,
        mime_type='application/pdf',
        processing_status='completed',
        source='upload',
        user_id=sample_document.user_id,
    )
    db.add(target)
    db.commit()

    rel = DocumentRelationshipReview(
        source_document_id=sample_document.id,
        target_document_id=target.id,
        relationship_type='similar',
        confidence=0.9,
        reason_codes_json=['model_detection'],
    )
    db.add(rel)
    db.commit()
    db.refresh(rel)
    return rel


def test_viewer_cannot_mutate_review_action_or_relationship(test_user, db, sample_document):
    test_user.role = "viewer"
    db.add(test_user)
    db.commit()
    review_item = DocumentReviewItem(id=uuid.uuid4(), document_id=sample_document.id, review_type='missing_tags', status='open', reason='needs review')
    action_item = DocumentActionItem(document_id=sample_document.id, content='Follow up')
    db.add_all([review_item, action_item])
    db.commit()
    db.refresh(action_item)
    rel = _seed_relationship_review(db, sample_document)

    with _client_for_user(db, test_user) as client:
        assert client.post(f'/api/v1/review/items/{review_item.id}/resolve', json={'note': 'x'}).status_code == 403
        assert client.post(f'/api/v1/action-items/{action_item.id}/complete').status_code == 403
        assert client.post(f'/api/v1/review/relationships/{rel.id}/confirm', json={'reason_codes_json': ['ok']}).status_code == 403
    app.dependency_overrides.clear()


def test_editor_and_admin_can_mutate_review_action_or_relationship(test_user, db, sample_document):
    for role in ['editor', 'admin']:
        test_user.role = role
        db.add(test_user)
        db.commit()

        review_item = DocumentReviewItem(id=uuid.uuid4(), document_id=sample_document.id, review_type='processing_issues', status='open', reason=f'needs review {role}')
        action_item = DocumentActionItem(document_id=sample_document.id, content=f'Follow up {role}')
        db.add_all([review_item, action_item])
        db.commit()
        db.refresh(action_item)
        rel = _seed_relationship_review(db, sample_document)

        with _client_for_user(db, test_user) as client:
            assert client.post(f'/api/v1/review/items/{review_item.id}/resolve', json={'note': 'done'}).status_code == 200
            assert client.post(f'/api/v1/action-items/{action_item.id}/complete').status_code == 200
            assert client.post(f'/api/v1/review/relationships/{rel.id}/confirm', json={'reason_codes_json': ['human_validated']}).status_code == 200
        app.dependency_overrides.clear()
