from uuid import uuid4

from app.models.document import Document
from app.workers.tasks import _set_document_enrichment_status


class _FakeDocQuery:
    def __init__(self, doc):
        self._doc = doc

    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        return self._doc


class _FakeDB:
    def __init__(self, doc):
        self._doc = doc

    def query(self, _model):
        return _FakeDocQuery(self._doc)

    def add(self, _obj):
        return None

    def commit(self):
        return None


def _build_doc():
    return Document(
        id=uuid4(),
        filename="sample.pdf",
        original_path="/tmp/sample.pdf",
        file_type="pdf",
        file_size=1,
        source="upload",
        extracted_metadata={},
    )


def test_relationships_complete_embeddings_pending_keeps_pending():
    doc = _build_doc()
    db = _FakeDB(doc)

    _set_document_enrichment_status(db, str(doc.id), "pending")
    _set_document_enrichment_status(db, str(doc.id), "complete", task_name="relationships")

    assert doc.enrichment_pending is True


def test_embeddings_complete_relationships_pending_keeps_pending():
    doc = _build_doc()
    db = _FakeDB(doc)

    _set_document_enrichment_status(db, str(doc.id), "pending")
    _set_document_enrichment_status(db, str(doc.id), "complete", task_name="embeddings")

    assert doc.enrichment_pending is True


def test_both_complete_sets_complete():
    doc = _build_doc()
    db = _FakeDB(doc)

    _set_document_enrichment_status(db, str(doc.id), "pending")
    _set_document_enrichment_status(db, str(doc.id), "complete", task_name="relationships")
    _set_document_enrichment_status(db, str(doc.id), "complete", task_name="embeddings")

    assert doc.enrichment_status == "complete"


def test_one_degraded_none_pending_sets_degraded():
    doc = _build_doc()
    db = _FakeDB(doc)

    _set_document_enrichment_status(db, str(doc.id), "pending")
    _set_document_enrichment_status(db, str(doc.id), "degraded", task_name="relationships")
    _set_document_enrichment_status(db, str(doc.id), "complete", task_name="embeddings")

    assert doc.enrichment_status == "degraded"
    assert doc.enrichment_pending is False


def test_one_degraded_while_other_pending_keeps_pending():
    doc = _build_doc()
    db = _FakeDB(doc)

    _set_document_enrichment_status(db, str(doc.id), "pending")
    _set_document_enrichment_status(db, str(doc.id), "degraded", task_name="relationships")

    assert doc.enrichment_pending is True
