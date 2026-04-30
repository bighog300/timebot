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
