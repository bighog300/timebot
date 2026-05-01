from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.services.document_intelligence import document_intelligence_service
from app.services.timeline_service import timeline_service


class FakeDB:
    def __init__(self, docs=None):
        self.docs = docs or []
    def query(self, _model):
        return FakeQuery(self.docs)
    def add(self, _):
        pass
    def commit(self):
        pass
    def refresh(self, _):
        pass


class FakeQuery:
    def __init__(self, items): self.items=list(items)
    def filter(self,*_,**__): return self
    def order_by(self,*_,**__): return self
    def limit(self,n): return FakeQuery(self.items[:n])
    def all(self): return self.items
    def first(self): return self.items[0] if self.items else None


def _doc():
    return SimpleNamespace(id=uuid4(), filename='a.pdf', entities={}, upload_date=datetime.now(timezone.utc), source='upload', file_type='pdf', is_archived=False, ai_category_id=None, user_category_id=None, extracted_metadata={}, user_id=uuid4())


def test_timeline_extraction_persists_events():
    doc = _doc()
    analysis = {'summary':'s','key_points':[],'tags':[],'entities':{},'action_items':[],'timeline_events':[{'title':'Deadline','date':'2026-05-01','confidence':0.9}]}
    db=FakeDB()
    document_intelligence_service._upsert_from_analysis(db, doc, analysis)
    assert doc.entities['timeline_events'][0]['title'] == 'Deadline'


def test_timeline_api_returns_extracted_events_only():
    doc = _doc()
    doc.entities={'timeline_events':[{'title':'Kickoff','date':'2026-06-01','confidence':0.8,'source':'extracted'}]}
    res = timeline_service.build_timeline(FakeDB([doc]))
    assert res['total_events'] == 1
    assert res['events'][0]['title'] == 'Kickoff'


def test_no_key_behavior_empty_timeline():
    doc = _doc(); doc.entities={}
    res = timeline_service.build_timeline(FakeDB([doc]))
    assert res['events'] == []


def test_upload_date_not_primary_event_date():
    doc = _doc(); doc.entities={}
    res = timeline_service.build_timeline(FakeDB([doc]))
    assert res['total_events'] == 0


def test_timeline_fallback_extracts_dates_from_text():
    doc = _doc()
    doc.entities = {}
    doc.raw_text = "Payment due date: February 15, 2025. Renewal deadline: 2025-11-30."
    res = timeline_service.build_timeline(FakeDB([doc]))
    assert res["total_events"] >= 2
    assert all(ev["source"] == "date_extraction_fallback" for ev in res["events"])


def test_thread_duplicate_timeline_events_are_not_inserted_twice():
    doc = _doc()
    doc.source = "gmail"
    doc.extracted_metadata = {"gmail_thread_id": "thread-123"}
    doc.entities = {"timeline_events": [{"title": "Project kickoff", "date": "2026-05-01"}]}
    analysis = {"summary": "s", "key_points": [], "tags": [], "entities": {}, "action_items": [], "timeline_events": [{"title": "Project kickoff", "date": "2026-05-01"}]}
    document_intelligence_service._upsert_from_analysis(FakeDB([doc]), doc, analysis)
    assert doc.entities["timeline_events"] == []


def test_distinct_timeline_events_are_preserved():
    doc = _doc()
    doc.entities = {"timeline_events": [{"title": "Kickoff", "date": "2026-05-01"}]}
    analysis = {"summary": "s", "key_points": [], "tags": [], "entities": {}, "action_items": [], "timeline_events": [{"title": "Launch", "date": "2026-06-10"}]}
    document_intelligence_service._upsert_from_analysis(FakeDB([doc]), doc, analysis)
    assert len(doc.entities["timeline_events"]) == 1
    assert doc.entities["timeline_events"][0]["title"] == "Launch"


def test_normalization_collapses_case_and_punctuation_duplicates():
    doc = _doc()
    doc.entities = {"timeline_events": [{"title": "Contract Signed", "date": "2026-05-01"}]}
    analysis = {"summary": "s", "key_points": [], "tags": [], "entities": {}, "action_items": [], "timeline_events": [{"title": "contract signed!!!", "date": "2026-05-01"}]}
    document_intelligence_service._upsert_from_analysis(FakeDB([doc]), doc, analysis)
    assert doc.entities["timeline_events"] == []
