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


def test_milestone_detected_for_keyword_event():
    doc = _doc()
    doc.entities = {"timeline_events": [{"title": "Contract Signed", "date": "2026-07-01", "confidence": 0.4}]}
    res = timeline_service.build_timeline(FakeDB([doc]))
    assert res["events"][0]["is_milestone"] is True
    assert "keyword" in (res["events"][0]["milestone_reason"] or "")


def test_milestone_detected_for_repeated_events_across_documents():
    doc_a = _doc()
    doc_a.entities = {"timeline_events": [{"title": "Launch Plan", "date": "2026-06-01", "confidence": 0.2}]}
    doc_b = _doc()
    doc_b.entities = {"timeline_events": [{"title": "launch plan!", "date": "2026-06-03", "confidence": 0.2}]}
    res = timeline_service.build_timeline(FakeDB([doc_a, doc_b]))
    assert res["total_events"] == 2
    assert all(event["is_milestone"] for event in res["events"])
    assert all("repeated_across_documents" in (event.get("milestone_reason") or "") for event in res["events"])


def test_non_milestone_event_remains_unflagged():
    doc = _doc()
    doc.entities = {"timeline_events": [{"title": "Status update", "date": "2026-09-01", "confidence": 0.3}]}
    res = timeline_service.build_timeline(FakeDB([doc]))
    assert res["events"][0]["is_milestone"] is False
    assert res["events"][0]["milestone_reason"] is None


def test_gaps_detected_for_spaced_events():
    doc = _doc()
    doc.entities = {"timeline_events": [
        {"title": "Kickoff", "date": "2026-01-01", "confidence": 0.8},
        {"title": "Review", "date": "2026-03-05", "confidence": 0.8},
    ]}
    res = timeline_service.build_timeline(FakeDB([doc]))
    assert len(res["gaps"]) == 1
    assert res["gaps"][0] == {"start_date": "2026-01-01", "end_date": "2026-03-05", "gap_duration_days": 63}


def test_no_gaps_when_events_are_dense():
    doc = _doc()
    doc.entities = {"timeline_events": [
        {"title": "Day 1", "date": "2026-01-01", "confidence": 0.8},
        {"title": "Day 2", "date": "2026-01-15", "confidence": 0.8},
        {"title": "Day 3", "date": "2026-01-28", "confidence": 0.8},
    ]}
    res = timeline_service.build_timeline(FakeDB([doc]))
    assert res["gaps"] == []


def test_gap_detection_safe_for_single_or_no_events():
    single = _doc()
    single.entities = {"timeline_events": [{"title": "Only event", "date": "2026-02-01", "confidence": 0.8}]}
    single_res = timeline_service.build_timeline(FakeDB([single]))
    assert single_res["gaps"] == []

    empty = _doc()
    empty.entities = {}
    empty_res = timeline_service.build_timeline(FakeDB([empty]))
    assert empty_res["gaps"] == []


def test_timeline_confidence_normalizes_to_unit_interval():
    doc = _doc()
    doc.entities = {"timeline_events": [{"title": "Percent Confidence", "date": "2026-08-01", "confidence": 85}]}
    res = timeline_service.build_timeline(FakeDB([doc]))
    assert res["events"][0]["confidence"] == 0.85


def test_timeline_signal_strength_label_mapping():
    doc = _doc()
    doc.entities = {
        "timeline_events": [
            {"title": "Strong", "date": "2026-01-01", "confidence": 0.9},
            {"title": "Medium", "date": "2026-01-02", "confidence": 0.6},
            {"title": "Weak", "date": "2026-01-03", "confidence": 0.2},
        ]
    }
    res = timeline_service.build_timeline(FakeDB([doc]))
    labels = [event["signal_strength"] for event in res["events"]]
    assert labels == ["strong", "medium", "weak"]


def test_timeline_missing_confidence_remains_safe():
    doc = _doc()
    doc.entities = {"timeline_events": [{"title": "Unknown", "date": "2026-08-02"}]}
    res = timeline_service.build_timeline(FakeDB([doc]))
    assert res["events"][0]["confidence"] is None
    assert res["events"][0]["signal_strength"] is None

def test_action_items_persist_to_document_from_analysis():
    doc = _doc()
    analysis = {'summary':'s','key_points':[],'tags':[],'entities':{},'action_items':['Submit signed form by 2026-05-10'],'timeline_events':[]}
    db=FakeDB()
    document_intelligence_service._upsert_from_analysis(db, doc, analysis)
    assert doc.action_items == ['Submit signed form by 2026-05-10']


def test_dict_tags_and_key_points_normalize_to_strings():
    doc = _doc()
    analysis = {
        "summary": "s",
        "key_points": [{"title": "Board approved budget"}],
        "tags": [{"name": "finance"}, {"label": "Q2"}],
        "entities": {},
        "action_items": [],
        "timeline_events": [],
    }
    document_intelligence_service._upsert_from_analysis(FakeDB(), doc, analysis)
    assert doc.key_points == ["Board approved budget"]
    assert doc.ai_tags == ["finance", "Q2"]


def test_structured_action_items_preserve_payload_and_do_not_crash():
    doc = _doc()
    analysis = {
        "summary": "s",
        "key_points": [],
        "tags": [],
        "entities": {},
        "action_items": [{"title": "File appeal", "due_date": "2026-06-01"}],
        "timeline_events": [],
    }
    document_intelligence_service._upsert_from_analysis(FakeDB(), doc, analysis)
    assert isinstance(doc.action_items[0], dict)
    assert doc.action_items[0]["content"] == "File appeal"
    assert doc.action_items[0]["due_date"] == "2026-06-01"


def test_normalization_warning_persisted_when_fallback_occurs():
    doc = _doc()
    analysis = {
        "summary": "s",
        "key_points": [{}],
        "tags": [123],
        "entities": [],
        "action_items": [None],
        "timeline_events": [],
    }
    document_intelligence_service._upsert_from_analysis(FakeDB(), doc, analysis)
    warnings = doc.extracted_metadata.get("intelligence_normalization_warnings", [])
    assert len(warnings) >= 3
    assert any(w.get("field_name") == "entities" for w in warnings)
