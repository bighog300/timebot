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
        calls = 0

        def create(self, **kwargs):
            self.calls += 1
            if self.calls == 1:
                return DummyResp()
            return type("DummyResp2", (), {"choices": [type("DummyChoice2", (), {"message": type("M", (), {"content": '{\"summary\":\"S\",\"timeline\":\"T\",\"relationships\":\"R\"}'})()})()]})()

    class DummyChat:
        completions = DummyComp()

    monkeypatch.setattr("app.config.settings.OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.api.v1.reports.openai_client_service._client", type("C", (), {"chat": DummyChat()})())
    res = client.post("/api/v1/reports", json={"title": "My Report", "prompt": "summarize", "document_ids": []})
    assert res.status_code == 200
    data = res.json()
    assert data["content_markdown"].startswith("# Report")
    assert data["sections"] == {"summary": "S", "timeline": "T", "relationships": "R"}
    get_res = client.get(data["download_url"])
    assert get_res.status_code == 200
    # remove file then ensure recreated
    from app.models.chat import GeneratedReport
    rep = db.query(GeneratedReport).first()
    assert rep.content_markdown.startswith("# Report")
    assert rep.sections == {"summary": "S", "timeline": "T", "relationships": "R"}
    Path(rep.file_path).unlink(missing_ok=True)
    get_res2 = client.get(data["download_url"])
    assert get_res2.status_code == 200


def test_report_sections_fallback_when_missing(client, monkeypatch, db):
    class DummyComp:
        calls = 0

        def create(self, **kwargs):
            self.calls += 1
            if self.calls == 1:
                return type("DR", (), {"choices": [type("DC", (), {"message": type("M", (), {"content": "# Report\\n\\nStill works"})()})()]})()
            return type("DR2", (), {"choices": [type("DC2", (), {"message": type("M", (), {"content": "not-json"})()})()]})()

    class DummyChat:
        completions = DummyComp()

    monkeypatch.setattr("app.config.settings.OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.api.v1.reports.openai_client_service._client", type("C", (), {"chat": DummyChat()})())

    created = client.post("/api/v1/reports", json={"title": "Fallback Report", "prompt": "summarize"}).json()
    assert created["sections"] is None
    assert created["content_markdown"].startswith("# Report")

    detail = client.get(f"/api/v1/reports/{created['id']}")
    assert detail.status_code == 200
    assert detail.json()["sections"] is None
    assert detail.json()["content_markdown"].startswith("# Report")


def test_report_owner_can_update_sections(client, monkeypatch):
    class DummyComp:
        calls = 0

        def create(self, **kwargs):
            self.calls += 1
            if self.calls == 1:
                return type("DR", (), {"choices": [type("DC", (), {"message": type("M", (), {"content": "# Report\n\nBody"})()})()]})()
            return type("DR2", (), {"choices": [type("DC2", (), {"message": type("M", (), {"content": '{"summary":"S","timeline":"T","relationships":"R"}'})()})()]})()

    monkeypatch.setattr("app.config.settings.OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.api.v1.reports.openai_client_service._client", type("C", (), {"chat": type("Chat", (), {"completions": DummyComp()})()})())
    created = client.post("/api/v1/reports", json={"title": "Editable", "prompt": "p"}).json()
    updated = client.patch(f"/api/v1/reports/{created['id']}", json={"sections": {"summary": "Updated S", "timeline": "Updated T", "relationships": "Updated R"}})
    assert updated.status_code == 200
    assert updated.json()["sections"]["summary"] == "Updated S"


def test_report_update_forbidden_for_other_user(client, db, monkeypatch):
    from app.models.user import User
    from app.services.auth import auth_service
    from app.api.deps import get_current_user
    from app.main import app

    class DummyComp:
        calls = 0

        def create(self, **kwargs):
            self.calls += 1
            if self.calls == 1:
                return type("DR", (), {"choices": [type("DC", (), {"message": type("M", (), {"content": "# Report\n\nBody"})()})()]})()
            return type("DR2", (), {"choices": [type("DC2", (), {"message": type("M", (), {"content": '{"summary":"S","timeline":"T","relationships":"R"}'})()})()]})()

    monkeypatch.setattr("app.config.settings.OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.api.v1.reports.openai_client_service._client", type("C", (), {"chat": type("Chat", (), {"completions": DummyComp()})()})())
    created = client.post("/api/v1/reports", json={"title": "Private", "prompt": "p"}).json()

    other = User(email="other@example.com", display_name="other", password_hash=auth_service.hash_password("pw"), is_active=True, role="editor")
    db.add(other)
    db.commit()
    app.dependency_overrides[get_current_user] = lambda: other
    res = client.patch(f"/api/v1/reports/{created['id']}", json={"sections": {"summary": "hack"}})
    app.dependency_overrides.pop(get_current_user, None)
    assert res.status_code == 404


def test_report_update_rejects_invalid_sections_payload(client, monkeypatch):
    class DummyComp:
        calls = 0

        def create(self, **kwargs):
            self.calls += 1
            if self.calls == 1:
                return type("DR", (), {"choices": [type("DC", (), {"message": type("M", (), {"content": "# Report\n\nBody"})()})()]})()
            return type("DR2", (), {"choices": [type("DC2", (), {"message": type("M", (), {"content": '{"summary":"S","timeline":"T","relationships":"R"}'})()})()]})()

    monkeypatch.setattr("app.config.settings.OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.api.v1.reports.openai_client_service._client", type("C", (), {"chat": type("Chat", (), {"completions": DummyComp()})()})())
    created = client.post("/api/v1/reports", json={"title": "Invalid", "prompt": "p"}).json()
    bad = client.patch(f"/api/v1/reports/{created['id']}", json={"sections": {"summary": 1}})
    assert bad.status_code == 422


def test_markdown_download_remains_after_section_edit(client, monkeypatch):
    class DummyComp:
        calls = 0

        def create(self, **kwargs):
            self.calls += 1
            if self.calls == 1:
                return type("DR", (), {"choices": [type("DC", (), {"message": type("M", (), {"content": "# Report\n\nBody"})()})()]})()
            return type("DR2", (), {"choices": [type("DC2", (), {"message": type("M", (), {"content": '{"summary":"S","timeline":"T","relationships":"R"}'})()})()]})()

    monkeypatch.setattr("app.config.settings.OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.api.v1.reports.openai_client_service._client", type("C", (), {"chat": type("Chat", (), {"completions": DummyComp()})()})())
    created = client.post("/api/v1/reports", json={"title": "Downloadable", "prompt": "p"}).json()
    patched = client.patch(f"/api/v1/reports/{created['id']}", json={"sections": {"summary": "Edited", "timeline": "T", "relationships": "R"}})
    assert patched.status_code == 200
    download = client.get(created["download_url"])
    assert download.status_code == 200
    assert "# Report" in download.text


def test_report_owner_can_download_pdf(client, monkeypatch):
    class DummyComp:
        calls = 0
        def create(self, **kwargs):
            self.calls += 1
            if self.calls == 1:
                return type("DR", (), {"choices": [type("DC", (), {"message": type("M", (), {"content": "# Report\n\nBody"})()})()]})()
            return type("DR2", (), {"choices": [type("DC2", (), {"message": type("M", (), {"content": '{"summary":"S","timeline":"T","relationships":"R"}'})()})()]})()
    monkeypatch.setattr("app.config.settings.OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.api.v1.reports.openai_client_service._client", type("C", (), {"chat": type("Chat", (), {"completions": DummyComp()})()})())
    created = client.post("/api/v1/reports", json={"title": "PDF Report", "prompt": "p"}).json()
    res = client.get(f"/api/v1/reports/{created['id']}/download?format=pdf")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("application/pdf")
    assert res.content.startswith(b"%PDF")


def test_report_pdf_download_forbidden_for_other_user(client, db, monkeypatch):
    from app.models.user import User
    from app.services.auth import auth_service
    from app.api.deps import get_current_user
    from app.main import app
    class DummyComp:
        calls = 0
        def create(self, **kwargs):
            self.calls += 1
            if self.calls == 1:
                return type("DR", (), {"choices": [type("DC", (), {"message": type("M", (), {"content": "# Report\n\nBody"})()})()]})()
            return type("DR2", (), {"choices": [type("DC2", (), {"message": type("M", (), {"content": '{"summary":"S","timeline":"T","relationships":"R"}'})()})()]})()
    monkeypatch.setattr("app.config.settings.OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.api.v1.reports.openai_client_service._client", type("C", (), {"chat": type("Chat", (), {"completions": DummyComp()})()})())
    created = client.post("/api/v1/reports", json={"title": "Private", "prompt": "p"}).json()
    other = User(email="other2@example.com", display_name="other2", password_hash=auth_service.hash_password("pw"), is_active=True, role="editor")
    db.add(other); db.commit()
    app.dependency_overrides[get_current_user] = lambda: other
    res = client.get(f"/api/v1/reports/{created['id']}/download?format=pdf")
    app.dependency_overrides.pop(get_current_user, None)
    assert res.status_code == 404


def test_report_pdf_prefers_structured_sections(client, monkeypatch):
    class DummyComp:
        calls = 0
        def create(self, **kwargs):
            self.calls += 1
            if self.calls == 1:
                return type("DR", (), {"choices": [type("DC", (), {"message": type("M", (), {"content": "# Report\n\nBody markdown only"})()})()]})()
            return type("DR2", (), {"choices": [type("DC2", (), {"message": type("M", (), {"content": '{"summary":"S section","timeline":"T section","relationships":"R section"}'})()})()]})()
    monkeypatch.setattr("app.config.settings.OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.api.v1.reports.openai_client_service._client", type("C", (), {"chat": type("Chat", (), {"completions": DummyComp()})()})())
    created = client.post("/api/v1/reports", json={"title": "Structured", "prompt": "p"}).json()
    _ = client.get(f"/api/v1/reports/{created['id']}/download?format=pdf")
    from app.config import settings
    pdf_path = Path(settings.effective_artifact_dir) / "reports" / f"{created['id']}.pdf"
    assert pdf_path.exists()
    raw = pdf_path.read_bytes()
    assert b"S section" in raw and b"T section" in raw and b"R section" in raw


def test_report_pdf_falls_back_to_markdown_when_sections_missing(client, monkeypatch):
    class DummyComp:
        calls = 0
        def create(self, **kwargs):
            self.calls += 1
            if self.calls == 1:
                return type("DR", (), {"choices": [type("DC", (), {"message": type("M", (), {"content": "# Report\\n\\nMarkdown fallback body"})()})()]})()
            return type("DR2", (), {"choices": [type("DC2", (), {"message": type("M", (), {"content": "not-json"})()})()]})()
    monkeypatch.setattr("app.config.settings.OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.api.v1.reports.openai_client_service._client", type("C", (), {"chat": type("Chat", (), {"completions": DummyComp()})()})())
    created = client.post("/api/v1/reports", json={"title": "Fallback", "prompt": "p"}).json()
    _ = client.get(f"/api/v1/reports/{created['id']}/download?format=pdf")
    from app.config import settings
    pdf_path = Path(settings.effective_artifact_dir) / "reports" / f"{created['id']}.pdf"
    assert b"Markdown fallback body" in pdf_path.read_bytes()


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


def test_format_chat_context_includes_labeled_sections_and_metadata(db, test_user):
    from app.models.relationships import DocumentRelationship
    from app.services.chat_retrieval import format_chat_context

    source = _mk_doc(
        db,
        test_user.id,
        "source.txt",
        "Source summary for alpha",
        {"timeline_events": [{"title": "Kickoff", "date": "2025-01-01", "description": "Project kickoff"}]},
    )
    target = _mk_doc(db, test_user.id, "target.txt", "Target summary")
    source.extracted_metadata = {
        "thread_outcome": {"status": "approved", "reason": "manager confirmed", "confidence": 0.92}
    }
    rel = DocumentRelationship(
        source_doc_id=source.id,
        target_doc_id=target.id,
        relationship_type="related_to",
        relationship_metadata={"explanation": {"reason": "same customer request", "signals": ["thread"]}},
    )
    db.add(rel)
    db.commit()

    ctx = retrieve_chat_context(db, "kickoff source related_to", test_user.id, None, True, False, 5)
    formatted = format_chat_context(ctx)

    assert "Document Summaries" in formatted
    assert "Timeline Events" in formatted
    assert "Relationships" in formatted
    assert "Email Thread Outcomes" in formatted
    assert "Full Text Excerpts" in formatted
    assert "source.txt" in formatted
    assert "[2025-01-01]" in formatted
    assert "explanation:" in formatted
    assert "approved" in formatted
    assert ctx["source_refs"]


def test_streaming_and_non_streaming_use_same_formatted_context(client, monkeypatch, db):
    from app.models.user import User

    user = db.query(User).first()
    _mk_doc(db, user.id, "alpha.txt", "Alpha summary with milestone")

    captured: dict[str, str] = {}

    class DummyChunk:
        def __init__(self, text):
            self.choices = [type("Choice", (), {"delta": type("Delta", (), {"content": text})()})()]

    class DummyComp:
        def create(self, **kwargs):
            user_prompt = kwargs["messages"][-1]["content"]
            if kwargs.get("stream"):
                captured["stream"] = user_prompt
                return [DummyChunk("stream"), DummyChunk("ed")]
            captured["non_stream"] = user_prompt
            return type("DummyResp", (), {"choices": [type("DummyChoice", (), {"message": type("M", (), {"content": "Grounded response"})()})()]})()

    class DummyChat:
        completions = DummyComp()

    monkeypatch.setattr("app.config.settings.OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.api.v1.chat.openai_client_service._client", type("C", (), {"chat": DummyChat()})())

    s = client.post("/api/v1/chat/sessions", json={"title": "ctx-shared"}).json()
    non_stream = client.post(f"/api/v1/chat/sessions/{s['id']}/messages", json={"message": "alpha"})
    assert non_stream.status_code == 200

    with client.stream("POST", f"/api/v1/chat/sessions/{s['id']}/messages/stream", json={"message": "alpha"}) as response:
        assert response.status_code == 200
        _ = "".join(list(response.iter_text()))

    assert "Context:\n" in captured["non_stream"]
    assert "Context:\n" in captured["stream"]
    non_stream_context = captured["non_stream"].split("Question:\n", 1)[0]
    stream_context = captured["stream"].split("Question:\n", 1)[0]
    assert non_stream_context == stream_context
