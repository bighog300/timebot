from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.services.query_parser import query_parser
from app.services.relationship_detection import RelationshipCandidate, relationship_detection_service
from app.services.search_service import search_service
from app.services.timeline_service import timeline_service
from app.services.insights_service import insights_service


class FakeDB:
    def __init__(self, docs=None, rels=None, categories=None):
        self.docs = docs or []
        self.rels = rels or []
        self.categories = categories or []

    def query(self, model):
        model_name = getattr(model, "__name__", str(model))
        if model_name == "Document":
            return FakeQuery(self.docs)
        if model_name == "DocumentRelationship":
            return FakeRelQuery(self.rels)
        if model_name == "Category":
            return FakeQuery(self.categories)
        return FakeQuery([])

    def add(self, item):
        if item.__class__.__name__ == "DocumentRelationship":
            self.rels.append(item)

    def commit(self):
        return None


class CountingDB(FakeDB):
    def __init__(self, docs=None, rels=None, categories=None):
        super().__init__(docs=docs, rels=rels, categories=categories)
        self.query_calls = 0

    def query(self, model):
        self.query_calls += 1
        return super().query(model)


class FakeQuery:
    def __init__(self, items):
        self.items = list(items)

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def limit(self, n):
        return FakeQuery(self.items[:n])

    def count(self):
        return len(self.items)

    def offset(self, _n):
        return self

    def all(self):
        return self.items


class FakeRelQuery(FakeQuery):
    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.items[0] if self.items else None


def _doc(name: str, *, tags=None, entities=None, days=0):
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=uuid4(),
        filename=name,
        summary=f"Summary for {name}",
        raw_text=f"Raw text mentions invoice and follow up for {name}",
        ai_tags=tags or [],
        user_tags=[],
        entities=entities or {},
        upload_date=now - timedelta(days=days),
        source="upload",
        file_type="pdf",
        is_archived=False,
        action_items=["TODO: follow up"] if "follow" in name else [],
        processing_status="completed",
        ai_category=None,
        user_category=None,
        ai_category_id=None,
        user_category_id=None,
        all_tags=tags or [],
    )


def test_query_parser_handles_phrases_and_exclusions():
    parsed = query_parser.parse('"board meeting" budget -draft')
    assert "board meeting" in parsed.phrases
    assert "budget" in parsed.terms
    assert "draft" in parsed.excluded_terms


def test_highlights_include_markdown_emphasis():
    doc = _doc("report.pdf")
    parsed = query_parser.parse("invoice")
    highlights = search_service._generate_highlights(doc, parsed)
    assert highlights
    assert "**invoice**" in highlights[0].lower()


def test_relationship_persistence_idempotent():
    db = FakeDB(rels=[])
    a = _doc("contract_v1.pdf", tags=["legal", "contract"], entities={"people": ["Alex"]})
    b = _doc("contract_v2.pdf", tags=["legal", "contract"], entities={"people": ["Alex"]}, days=1)

    candidate = relationship_detection_service._score_pair(a, b)
    assert candidate is not None

    first = relationship_detection_service._persist_candidates(db, [candidate])
    second = relationship_detection_service._persist_candidates(db, [candidate])

    assert first["created"] == 1
    assert second["created"] == 0




def test_relationship_follows_up_creates_review_item(db, sample_document):
    from app.models.document import Document
    from app.models.intelligence import DocumentRelationshipReview

    source = sample_document
    target = Document(
        filename="incident-follow-up.pdf",
        original_path="/tmp/incident-follow-up.pdf",
        file_type="pdf",
        file_size=100,
        user_id=source.user_id,
        processing_status="completed",
        source="upload",
        is_archived=False,
        entities=source.entities,
        upload_date=source.upload_date,
    )
    db.add(target)
    db.commit()
    db.refresh(target)

    candidate = RelationshipCandidate(
        source_doc_id=source.id,
        target_doc_id=target.id,
        relationship_type="follows_up",
        confidence=0.7,
        metadata={"signals": {"date_adjacency": 1.0}},
    )

    relationship_detection_service._persist_candidates(db, [candidate])

    review = db.query(DocumentRelationshipReview).filter(DocumentRelationshipReview.source_document_id == candidate.source_doc_id).first()
    assert review is not None
    assert review.relationship_type == "related"
    assert review.status == "pending"
def test_timeline_response_shape():
    docs = [_doc("d1.pdf", entities={"dates": ["2026-01-01"]}), _doc("d2.pdf", days=3)]
    db = FakeDB(docs=docs)
    timeline = timeline_service.build_timeline(db=db, group_by="week")
    assert timeline["group_by"] == "week"
    assert "buckets" in timeline
    assert isinstance(timeline["buckets"], list)


def test_insights_response_shape():
    docs = [_doc("followup.pdf", days=1), _doc("notes.pdf", days=2)]
    db = FakeDB(docs=docs, rels=[], categories=[])
    insights = insights_service.build_dashboard(db=db, lookback_days=30)
    assert "volume_trends" in insights
    assert "relationship_summary" in insights
    assert "recent_activity" in insights




def test_insights_response_shape_handles_mixed_naive_and_aware_upload_dates():
    docs = [_doc("aware.pdf", days=1), _doc("naive.pdf", days=2)]
    docs[1].upload_date = docs[1].upload_date.replace(tzinfo=None)

    db = FakeDB(docs=docs, rels=[], categories=[])
    insights = insights_service.build_dashboard(db=db, lookback_days=30)

    assert "volume_trends" in insights
    assert "relationship_summary" in insights
    assert "recent_activity" in insights
    assert len(insights["recent_activity"]) == 2
def test_hybrid_search_degrades_when_semantic_unavailable(monkeypatch):
    fake_doc = _doc("invoice.pdf")

    class FakeQueryForHybrid(FakeQuery):
        def count(self):
            return 1

        def offset(self, n):
            return self

    class HybridDB(FakeDB):
        def query(self, model):
            return FakeQueryForHybrid([fake_doc])

    db = HybridDB(docs=[fake_doc])
    monkeypatch.setattr("app.services.search_service.embedding_service._enabled", False)

    result = search_service.hybrid_search_documents(db=db, query="invoice", limit=5)
    assert result["degraded"] is True
    assert result["total"] >= 1


def test_search_documents_normalizes_invalid_paging_values():
    doc = _doc("invoice.pdf")
    db = FakeDB(docs=[doc])

    result = search_service.search_documents(db=db, query="invoice", skip=-5, limit=0)

    assert result["page"] == 1
    assert result["total"] >= 1


def test_hybrid_search_avoids_requery_when_semantic_disabled(monkeypatch):
    doc = _doc("invoice.pdf")
    db = CountingDB(docs=[doc])
    monkeypatch.setattr("app.services.search_service.embedding_service._enabled", False)

    result = search_service.hybrid_search_documents(db=db, query="invoice", limit=5)

    assert result["degraded"] is True
    assert db.query_calls == 1
