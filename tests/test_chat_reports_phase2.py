import uuid
from pathlib import Path

from app.api.v1.admin import _get_or_create_chatbot_settings
from app.services.chat_retrieval import retrieve_chat_context
from app.config import settings
from app.models.document import Document


def _mk_doc(db, user_id, filename, summary, entities=None):
    doc = Document(
        id=uuid.uuid4(), filename=filename, original_path=f"/tmp/{filename}", file_type="txt", file_size=10,
        mime_type="text/plain", processing_status="completed", source="upload", summary=summary,
        entities=entities or {}, action_items=[], key_points=[], ai_tags=[], user_id=user_id
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def test_retrieval_summary_and_filter(db, test_user):
    d1 = _mk_doc(db, test_user.id, "alpha.txt", "Project alpha budget and scope")
    _mk_doc(db, test_user.id, "beta.txt", "Completely unrelated")
    out = retrieve_chat_context(db, "alpha budget", test_user.id, [str(d1.id)], True, False, 5)
    assert out["documents"]
    assert out["documents"][0]["document_id"] == str(d1.id)


def test_retrieval_timeline_and_access_control(db, test_user):
    doc = _mk_doc(db, test_user.id, "timeline.txt", "Roadmap", {"timeline_events": [{"title": "Kickoff", "date": "2025-01-01", "description": "Project kickoff"}]})
    other = _mk_doc(db, uuid.uuid4(), "hidden.txt", "secret alpha")
    out = retrieve_chat_context(db, "kickoff", test_user.id, None, True, False, 5)
    assert any(d["document_id"] == str(doc.id) for d in out["documents"])
    assert all(d["document_id"] != str(other.id) for d in out["documents"])
    assert any(r["kind"] == "timeline_event" for r in out["source_refs"])


def test_retrieval_full_text_gate(db, test_user):
    doc = _mk_doc(db, test_user.id, "full.txt", "tiny")
    p = Path(settings.effective_artifact_dir) / "extracted_text" / "2026/04/30"
    p.mkdir(parents=True, exist_ok=True)
    (p / f"{doc.id}.txt").write_text("Important contract clause payment due now", encoding="utf-8")
    out = retrieve_chat_context(db, "payment", test_user.id, None, True, False, 5)
    assert not any(r["kind"] == "full_text_excerpt" for r in out["source_refs"])
    out2 = retrieve_chat_context(db, "payment", test_user.id, None, True, True, 5)
    assert any(r["kind"] == "full_text_excerpt" for r in out2["source_refs"])


def test_chat_endpoint_503_when_openai_missing(client, monkeypatch):
    monkeypatch.setattr("app.config.settings.OPENAI_API_KEY", "")
    s = client.post("/api/v1/chat/sessions", json={"title": "s"}).json()
    r = client.post(f"/api/v1/chat/sessions/{s['id']}/messages", json={"message": "hello"})
    assert r.status_code == 503


def test_chat_persists_and_returns_grounded(client, monkeypatch, db):
    from app.models.user import User
    user = db.query(User).first()
    _mk_doc(db, user.id, "alpha.txt", "Alpha summary with milestone")

    class DummyChoice:
        message = type("M", (), {"content": "According to \"alpha.txt\" details."})

    class DummyResp:
        choices = [DummyChoice()]

    class DummyComp:
        def create(self, **kwargs):
            return DummyResp()

    class DummyChat:
        completions = DummyComp()

    monkeypatch.setattr("app.config.settings.OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.api.v1.chat.openai_client_service._client", type("C", (), {"chat": DummyChat()})())
    s = client.post("/api/v1/chat/sessions", json={"title": "s"}).json()
    r = client.post(f"/api/v1/chat/sessions/{s['id']}/messages", json={"message": "alpha"})
    assert r.status_code == 200
    body = r.json()
    assert "Sources:" in body["message"]
    assert isinstance(body["source_refs"], list)



def test_chat_includes_recent_history_and_grounding_context(client, monkeypatch, db):
    from app.models.user import User

    user = db.query(User).first()
    _mk_doc(db, user.id, "alpha.txt", "Alpha summary with milestone")

    captured = {}

    class DummyChoice:
        message = type("M", (), {"content": "Grounded response"})

    class DummyResp:
        choices = [DummyChoice()]

    class DummyComp:
        def create(self, **kwargs):
            captured["messages"] = kwargs["messages"]
            return DummyResp()

    class DummyChat:
        completions = DummyComp()

    monkeypatch.setattr("app.config.settings.OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.api.v1.chat.openai_client_service._client", type("C", (), {"chat": DummyChat()})())

    s = client.post("/api/v1/chat/sessions", json={"title": "history"}).json()
    client.post(f"/api/v1/chat/sessions/{s['id']}/messages", json={"message": "alpha first question"})
    client.post(f"/api/v1/chat/sessions/{s['id']}/messages", json={"message": "alpha follow-up question"})

    msgs = captured["messages"]
    assert msgs[0]["role"] == "system"
    assert any(m["role"] == "assistant" and "Grounded response" in m["content"] for m in msgs)
    prompt_msg = msgs[-1]
    assert prompt_msg["role"] == "user"
    assert "Context:" in prompt_msg["content"]
    assert "Question:\nalpha follow-up question" in prompt_msg["content"]


def test_chat_history_is_capped_to_configured_max(client, monkeypatch, db):
    from app.models.user import User

    user = db.query(User).first()
    _mk_doc(db, user.id, "alpha.txt", "Alpha summary with milestone")

    captured = {}

    class DummyChoice:
        message = type("M", (), {"content": "Grounded response"})

    class DummyResp:
        choices = [DummyChoice()]

    class DummyComp:
        def create(self, **kwargs):
            captured["messages"] = kwargs["messages"]
            return DummyResp()

    class DummyChat:
        completions = DummyComp()

    monkeypatch.setattr("app.config.settings.OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.config.settings.CHAT_MAX_HISTORY_MESSAGES", 2)
    monkeypatch.setattr("app.api.v1.chat.openai_client_service._client", type("C", (), {"chat": DummyChat()})())

    s = client.post("/api/v1/chat/sessions", json={"title": "cap"}).json()
    client.post(f"/api/v1/chat/sessions/{s['id']}/messages", json={"message": "alpha q1"})
    client.post(f"/api/v1/chat/sessions/{s['id']}/messages", json={"message": "alpha q2"})
    client.post(f"/api/v1/chat/sessions/{s['id']}/messages", json={"message": "alpha q3"})

    history = captured["messages"][1:-1]
    assert len(history) == 2
    assert [m["role"] for m in history] == ["assistant", "user"]


def test_chat_stream_uses_same_history_behavior(client, monkeypatch, db):
    from app.models.user import User

    user = db.query(User).first()
    _mk_doc(db, user.id, "alpha.txt", "Alpha summary with milestone")

    captured = {}

    class DummyChunk:
        def __init__(self, text):
            self.choices = [type("Choice", (), {"delta": type("Delta", (), {"content": text})()})()]

    class DummyComp:
        def create(self, **kwargs):
            captured["messages"] = kwargs["messages"]
            if kwargs.get("stream"):
                return [DummyChunk("streamed "), DummyChunk("answer")]
            return type("DummyResp", (), {"choices": [type("DummyChoice", (), {"message": type("M", (), {"content": "Grounded response"})()})()]})()

    class DummyChat:
        completions = DummyComp()

    monkeypatch.setattr("app.config.settings.OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.api.v1.chat.openai_client_service._client", type("C", (), {"chat": DummyChat()})())

    s = client.post("/api/v1/chat/sessions", json={"title": "stream-history"}).json()
    client.post(f"/api/v1/chat/sessions/{s['id']}/messages", json={"message": "alpha first"})

    with client.stream("POST", f"/api/v1/chat/sessions/{s['id']}/messages/stream", json={"message": "alpha second"}) as response:
        assert response.status_code == 200
        _ = "".join(list(response.iter_text()))

    msgs = captured["messages"]
    assert any(m["role"] == "assistant" for m in msgs)
    assert "Question:\nalpha second" in msgs[-1]["content"]

def test_report_create_and_download_rebuild(client, monkeypatch, db):
    from app.models.user import User
    user = db.query(User).first()
    _mk_doc(db, user.id, "report_doc.txt", "Report source summary")

    class DummyChoice:
        message = type("M", (), {"content": "# Report\n\nGrounded text"})

    class DummyResp:
        choices = [DummyChoice()]

    class DummyComp:
        def create(self, **kwargs):
            return DummyResp()

    class DummyChat:
        completions = DummyComp()

    monkeypatch.setattr("app.config.settings.OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.api.v1.reports.openai_client_service._client", type("C", (), {"chat": DummyChat()})())
    res = client.post("/api/v1/reports", json={"title": "My Report", "prompt": "summarize", "document_ids": []})
    assert res.status_code == 200
    data = res.json()
    get_res = client.get(data["download_url"])
    assert get_res.status_code == 200
    # remove file then ensure recreated
    from app.models.chat import GeneratedReport
    rep = db.query(GeneratedReport).first()
    Path(rep.file_path).unlink(missing_ok=True)
    get_res2 = client.get(data["download_url"])
    assert get_res2.status_code == 200


def test_chat_stream_requires_auth():
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as unauth_client:
        res = unauth_client.post(f"/api/v1/chat/sessions/{uuid.uuid4()}/messages/stream", json={"message": "hello"})
    assert res.status_code == 401


def test_chat_stream_emits_chunks_and_persists_with_sources(client, monkeypatch, db):
    from app.models.chat import ChatMessage
    from app.models.user import User

    user = db.query(User).first()
    _mk_doc(db, user.id, "alpha.txt", "Alpha summary with milestone")

    class DummyChunk:
        def __init__(self, text):
            self.choices = [type("Choice", (), {"delta": type("Delta", (), {"content": text})()})()]

    class DummyComp:
        def create(self, **kwargs):
            if kwargs.get("stream"):
                for part in ["According ", "to alpha"]:
                    yield DummyChunk(part)
                return
            return type("DummyResp", (), {"choices": [type("DummyChoice", (), {"message": type("M", (), {"content": "According to alpha"})()})()]})()

    class DummyChat:
        completions = DummyComp()

    monkeypatch.setattr("app.config.settings.OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.api.v1.chat.openai_client_service._client", type("C", (), {"chat": DummyChat()})())

    s = client.post("/api/v1/chat/sessions", json={"title": "stream"}).json()
    with client.stream("POST", f"/api/v1/chat/sessions/{s['id']}/messages/stream", json={"message": "alpha"}) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        body = "".join(list(response.iter_text()))

    assert 'event: chunk' in body
    assert '"delta": "According "' in body
    assert '"delta": "to alpha"' in body
    assert 'event: final' in body
    assert '"source_refs"' in body

    msgs = db.query(ChatMessage).filter(ChatMessage.session_id == s["id"]).order_by(ChatMessage.created_at.asc()).all()
    assert len(msgs) == 2
    assert msgs[0].role == "user"
    assert msgs[1].role == "assistant"
    assert "Sources:" in msgs[1].content
    assert isinstance(msgs[1].source_refs, list)


def test_chat_success_emits_structured_log_without_message_content(client, monkeypatch, db, caplog):
    from app.models.user import User

    user = db.query(User).first()
    _mk_doc(db, user.id, "alpha.txt", "Alpha summary with milestone")

    class DummyChoice:
        message = type("M", (), {"content": "Grounded response"})

    class DummyResp:
        choices = [DummyChoice()]

    class DummyComp:
        def create(self, **kwargs):
            return DummyResp()

    class DummyChat:
        completions = DummyComp()

    monkeypatch.setattr("app.config.settings.OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.api.v1.chat.openai_client_service._client", type("C", (), {"chat": DummyChat()})())

    s = client.post("/api/v1/chat/sessions", json={"title": "log-s"}).json()
    raw_message = "private user message should not be logged"

    with caplog.at_level("INFO", logger="app.api.v1.chat"):
        r = client.post(f"/api/v1/chat/sessions/{s['id']}/messages", json={"message": raw_message})

    assert r.status_code == 200
    records = [rec for rec in caplog.records if rec.msg == "chat_request"]
    assert records
    rec = records[-1]
    assert rec.event == "chat_request"
    assert rec.endpoint_type == "non_streaming"
    assert rec.success is True
    assert rec.session_id == s["id"]
    assert rec.user_id
    assert isinstance(rec.retrieval_count, int)
    assert isinstance(rec.history_message_count, int)
    assert isinstance(rec.latency_ms, float)
    assert raw_message not in caplog.text


def test_chat_failure_emits_structured_log(client, monkeypatch, db, caplog):
    from app.models.user import User

    user = db.query(User).first()
    _mk_doc(db, user.id, "alpha.txt", "Alpha summary with milestone")

    class DummyComp:
        def create(self, **kwargs):
            raise Exception("simulated upstream failure")

    class DummyChat:
        completions = DummyComp()

    monkeypatch.setattr("app.config.settings.OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.api.v1.chat.APIError", Exception)
    monkeypatch.setattr("app.api.v1.chat.openai_client_service._client", type("C", (), {"chat": DummyChat()})())

    s = client.post("/api/v1/chat/sessions", json={"title": "log-f"}).json()
    with caplog.at_level("INFO", logger="app.api.v1.chat"):
        r = client.post(f"/api/v1/chat/sessions/{s['id']}/messages", json={"message": "alpha"})

    assert r.status_code == 503
    records = [rec for rec in caplog.records if rec.msg == "chat_request"]
    assert records
    rec = records[-1]
    assert rec.endpoint_type == "non_streaming"
    assert rec.success is False


def test_chat_stream_success_emits_structured_log(client, monkeypatch, db, caplog):
    from app.models.user import User

    user = db.query(User).first()
    _mk_doc(db, user.id, "alpha.txt", "Alpha summary with milestone")

    class DummyChunk:
        def __init__(self, text):
            self.choices = [type("Choice", (), {"delta": type("Delta", (), {"content": text})()})()]

    class DummyComp:
        def create(self, **kwargs):
            if kwargs.get("stream"):
                return [DummyChunk("hello "), DummyChunk("world")]
            return type("DummyResp", (), {"choices": [type("DummyChoice", (), {"message": type("M", (), {"content": "fallback"})()})()]})()

    class DummyChat:
        completions = DummyComp()

    monkeypatch.setattr("app.config.settings.OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.api.v1.chat.openai_client_service._client", type("C", (), {"chat": DummyChat()})())

    s = client.post("/api/v1/chat/sessions", json={"title": "stream-log"}).json()
    with caplog.at_level("INFO", logger="app.api.v1.chat"):
        with client.stream("POST", f"/api/v1/chat/sessions/{s['id']}/messages/stream", json={"message": "alpha"}) as response:
            assert response.status_code == 200
            _ = "".join(list(response.iter_text()))

    records = [rec for rec in caplog.records if rec.msg == "chat_request"]
    assert records
    rec = records[-1]
    assert rec.endpoint_type == "streaming"
    assert rec.success is True
