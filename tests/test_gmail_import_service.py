import base64
import uuid

from app.models.document import Document
from app.models.intelligence import DocumentRelationshipReview
from app.models.relationships import Connection, DocumentRelationship
from app.services.gmail_import import gmail_import_service


def _b64(s: str) -> str:
    return base64.urlsafe_b64encode(s.encode()).decode().rstrip('=')


def _msg_payload(mid='m1', plain='Hello\n-- \nSig', html='<p>Hello</p>', include_pdf=False, include_exe=False):
    parts = []
    if plain is not None:
        parts.append({"mimeType": "text/plain", "body": {"data": _b64(plain)}})
    if html is not None:
        parts.append({"mimeType": "text/html", "body": {"data": _b64(html)}})
    if include_pdf:
        parts.append({"mimeType": "application/pdf", "filename": "a.pdf", "body": {"attachmentId": "att1"}})
    if include_exe:
        parts.append({"mimeType": "application/octet-stream", "filename": "x.exe", "body": {"attachmentId": "att2"}})
    return {"id": mid, "threadId": "t1", "snippet": "snip", "payload": {"mimeType": "multipart/mixed", "headers": [{"name": "Subject", "value": "Subj"}, {"name": "From", "value": "f@example.com"}, {"name": "To", "value": "t@example.com"}, {"name": "Date", "value": "Thu"}], "parts": [{"mimeType": "multipart/alternative", "parts": parts}]}}


class FakeResp:
    def __init__(self, data): self._data = data
    def raise_for_status(self): return None
    def json(self): return self._data


class FakeClient:
    def __init__(self, *a, **kw): pass
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def get(self, url, params=None, headers=None):
        if url.endswith('/messages'):
            return FakeResp({"messages": [{"id": "m1"}]})
        if '/attachments/' in url:
            return FakeResp({"data": _b64('pdf bytes')})
        mid = url.rstrip('/').split('/')[-1]
        return FakeResp(_msg_payload(mid=mid))


def setup_conn(db, user):
    c = Connection(id=uuid.uuid4(), user_id=user.id, type='gmail', display_name='Gmail', status='connected', access_token='tok', token_scopes=[gmail_import_service.scope], is_authenticated=True)
    db.add(c); db.commit(); db.refresh(c)
    return c


def test_import_and_cleanup(db, test_user, monkeypatch):
    setup_conn(db, test_user)
    monkeypatch.setattr('app.services.gmail_import.connector_token_crypto.decrypt', lambda _: 't')
    monkeypatch.setattr('app.services.gmail_import.httpx.Client', FakeClient)
    monkeypatch.setattr('app.services.gmail_import.document_processor._process_sync', lambda *_: None)
    res = gmail_import_service.import_messages(db, test_user, 'f@example.com', ['m1'], include_attachments=False)
    assert res['imported_email_count'] == 1
    doc = db.query(Document).filter(Document.source_id == 'm1').first()
    assert 'Subject: Subj' in (doc.raw_text or '')
    assert 'Sent from my iPhone' not in (doc.raw_text or '')


def test_attachment_import_and_skip_and_duplicates(db, test_user, monkeypatch):
    setup_conn(db, test_user)
    monkeypatch.setattr('app.services.gmail_import.connector_token_crypto.decrypt', lambda _: 't')
    monkeypatch.setattr('app.services.gmail_import.document_processor._process_sync', lambda *_: None)

    class Client2(FakeClient):
        def get(self, url, params=None, headers=None):
            if '/messages/' in url and '/attachments/' not in url and params and params.get('format') == 'full':
                return FakeResp(_msg_payload(include_pdf=True, include_exe=True, plain='Top\nOn A wrote:\nquoted'))
            return super().get(url, params=params, headers=headers)

    monkeypatch.setattr('app.services.gmail_import.httpx.Client', Client2)
    res = gmail_import_service.import_messages(db, test_user, 'f@example.com', ['m1'], include_attachments=True)
    assert res['imported_attachment_count'] == 1
    assert res['skipped_attachment_count'] >= 1
    res2 = gmail_import_service.import_messages(db, test_user, 'f@example.com', ['m1'], include_attachments=True)
    assert res2['duplicate_message_count'] == 1
    email_doc = db.query(Document).filter(Document.source_id == "m1").first()
    attachment_doc = db.query(Document).filter(Document.source_id.like("m1:%")).first()
    rel = db.query(DocumentRelationship).filter(
        DocumentRelationship.source_doc_id == email_doc.id,
        DocumentRelationship.target_doc_id == attachment_doc.id,
        DocumentRelationship.relationship_type == "attachment",
    ).first()
    assert rel is not None
    assert rel.confidence == 1.0
    review = db.query(DocumentRelationshipReview).filter(
        DocumentRelationshipReview.source_document_id == email_doc.id,
        DocumentRelationshipReview.target_document_id == attachment_doc.id,
        DocumentRelationshipReview.relationship_type == "attachment",
    ).first()
    assert review is not None
    assert review.status == "confirmed"


def test_thread_relationship_created_and_deduplicated(db, test_user, monkeypatch):
    setup_conn(db, test_user)
    monkeypatch.setattr('app.services.gmail_import.connector_token_crypto.decrypt', lambda _: 't')
    monkeypatch.setattr('app.services.gmail_import.httpx.Client', FakeClient)
    monkeypatch.setattr('app.services.gmail_import.document_processor._process_sync', lambda *_: None)

    gmail_import_service.import_messages(db, test_user, 'f@example.com', ['m1', 'm2'], include_attachments=False)
    gmail_import_service.import_messages(db, test_user, 'f@example.com', ['m2'], include_attachments=False)
    docs = db.query(Document).filter(Document.source_id.in_(("m1", "m2"))).all()
    doc_map = {d.source_id: d for d in docs}
    source_id, target_id = (doc_map["m1"].id, doc_map["m2"].id) if str(doc_map["m1"].id) < str(doc_map["m2"].id) else (doc_map["m2"].id, doc_map["m1"].id)
    rels = db.query(DocumentRelationship).filter(
        DocumentRelationship.source_doc_id == source_id,
        DocumentRelationship.target_doc_id == target_id,
        DocumentRelationship.relationship_type == "thread",
    ).all()
    assert len(rels) == 1
    assert rels[0].confidence >= 0.9
