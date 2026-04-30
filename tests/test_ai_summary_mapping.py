from app.services.ai_analyzer import ai_analyzer


def test_normalize_analysis_accepts_executive_summary_alias():
    payload = {"executive_summary": "Alias summary", "key_points": [], "entities": {}, "tags": [], "action_items": []}
    normalized = ai_analyzer._normalize_analysis(payload)
    assert normalized["summary"] == "Alias summary"


def test_normalize_analysis_accepts_nested_analysis_summary():
    payload = {"analysis": {"summary": "Nested summary"}}
    normalized = ai_analyzer._normalize_analysis(payload)
    assert normalized["summary"] == "Nested summary"
    assert normalized["timeline_events"] == []


def test_normalize_analysis_accepts_timeline_aliases_and_dates():
    payload = {
        "important_dates": [
            {"name": "Renewal deadline", "due_date": "30 April 2026", "quote": "Renew by 30 April 2026", "page": 2},
            {"event_title": "Q2 phase", "event_date": "Q2 2026"},
        ]
    }
    normalized = ai_analyzer._normalize_analysis(payload)
    assert len(normalized["timeline_events"]) == 2
    assert normalized["timeline_events"][0]["title"] == "Renewal deadline"
    assert normalized["timeline_events"][0]["date"] == "2026-04-30"
    assert normalized["timeline_events"][1]["start_date"] == "2026-04-01"
