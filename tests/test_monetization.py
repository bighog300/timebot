import uuid

from app.models.billing import Plan, Subscription
from app.models.chat import AssistantProfile
from app.models.user import User
from app.services.subscriptions import seed_default_plans


def _set_plan(db, user, slug: str, status: str = "active"):
    seed_default_plans(db)
    mapped = {"business": "pro", "admin": "pro"}.get(slug, slug)
    plan = db.query(Plan).filter(Plan.slug == mapped).first()
    db.query(Subscription).filter(Subscription.user_id == user.id).delete()
    db.add(Subscription(user_id=user.id, plan_id=plan.id, status=status, external_provider="test"))
    user.plan = slug
    user.subscription_status = status
    db.add(user)
    db.commit()


def _mk_assistant(db, required_plan: str = "pro"):
    a = AssistantProfile(name=f"Pro Assistant {uuid.uuid4()}", description="x", required_plan=required_plan, enabled=True)
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


def test_free_user_sees_pro_assistant_locked_in_catalog(client, db, test_user):
    _set_plan(db, test_user, "free")
    assistant = _mk_assistant(db, "pro")
    resp = client.get("/api/v1/chat/assistants")
    assert resp.status_code == 200
    row = next(item for item in resp.json() if item["id"] == str(assistant.id))
    assert row["locked"] is True


def test_free_user_cannot_create_session_with_pro_assistant(client, db, test_user):
    _set_plan(db, test_user, "free")
    assistant = _mk_assistant(db, "pro")
    resp = client.post("/api/v1/chat/sessions", json={"title": "x", "assistant_id": str(assistant.id)})
    assert resp.status_code == 402
    assert resp.json()["detail"]["error"] == "upgrade_required"


def test_pro_user_can_create_session_with_pro_assistant(client, db, test_user):
    _set_plan(db, test_user, "pro")
    assistant = _mk_assistant(db, "pro")
    resp = client.post("/api/v1/chat/sessions", json={"title": "x", "assistant_id": str(assistant.id)})
    assert resp.status_code == 200


def test_admin_user_bypasses_entitlement_lock(client, db, test_user):
    _set_plan(db, test_user, "free")
    test_user.role = "admin"
    db.commit()
    assistant = _mk_assistant(db, "pro")
    resp = client.post("/api/v1/chat/sessions", json={"title": "x", "assistant_id": str(assistant.id)})
    assert resp.status_code == 200


def test_free_user_message_limit_returns_upgrade_required(client, db, test_user, monkeypatch):
    _set_plan(db, test_user, "free")
    monkeypatch.setattr("app.services.entitlements.get_usage_total", lambda *args, **kwargs: 999999)
    s = client.post("/api/v1/chat/sessions", json={"title": "x"}).json()
    resp = client.post(f"/api/v1/chat/sessions/{s['id']}/messages", json={"message": "hello"})
    assert resp.status_code == 402
    assert resp.json()["detail"]["error"] == "upgrade_required"


def test_non_pro_chat_metadata_excludes_system_refs(client, db, test_user, monkeypatch):
    _set_plan(db, test_user, "free")
    monkeypatch.setattr("app.config.settings.OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.api.v1.chat.openai_client_service._client", type("C", (), {"chat": type("Chat", (), {"completions": type("Comp", (), {"create": lambda self, **kwargs: type("R", (), {"choices": [type("Choice", (), {"message": type("M", (), {"content": "ok"})()})()]})()})()})()})())
    s = client.post("/api/v1/chat/sessions", json={"title": "x"}).json()
    r = client.post(f"/api/v1/chat/sessions/{s['id']}/messages", json={"message": "hello"})
    assert r.status_code == 200
    from app.models.chat import ChatMessage
    md = db.query(ChatMessage).filter(ChatMessage.session_id == s["id"], ChatMessage.role == "assistant").order_by(ChatMessage.created_at.desc()).first().metadata_json or {}
    assert md.get("system_intelligence_refs") in (None, [])
    assert md.get("legal_web_refs") in (None, [])


def test_pro_chat_metadata_includes_system_refs(client, db, test_user, monkeypatch):
    _set_plan(db, test_user, "pro")
    monkeypatch.setattr("app.config.settings.OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.api.v1.chat.openai_client_service._client", type("C", (), {"chat": type("Chat", (), {"completions": type("Comp", (), {"create": lambda self, **kwargs: type("R", (), {"choices": [type("Choice", (), {"message": type("M", (), {"content": "ok"})()})()]})()})()})()})())
    s = client.post("/api/v1/chat/sessions", json={"title": "x"}).json()
    r = client.post(f"/api/v1/chat/sessions/{s['id']}/messages", json={"message": "hello"})
    assert r.status_code == 200
    from app.models.chat import ChatMessage
    md = db.query(ChatMessage).filter(ChatMessage.session_id == s["id"], ChatMessage.role == "assistant").order_by(ChatMessage.created_at.desc()).first().metadata_json or {}
    assert "system_intelligence_refs" in md
    assert "legal_web_refs" in md


def test_free_user_custom_prompt_template_gated(client, db, test_user):
    _set_plan(db, test_user, "free")
    resp = client.post("/api/v1/chat/sessions", json={"title": "x", "prompt_template_id": str(uuid.uuid4())})
    assert resp.status_code == 402
    assert resp.json()["detail"]["feature"] == "custom_prompts"


def test_free_user_report_export_gated_pdf(client, db, test_user, monkeypatch):
    from app.models.chat import GeneratedReport
    _set_plan(db, test_user, "free")
    report = GeneratedReport(title="t", prompt="p", content_markdown="# x", sections={}, source_document_ids=[], source_refs=[], created_by_id=test_user.id)
    db.add(report)
    db.commit()
    db.refresh(report)
    resp = client.get(f"/api/v1/reports/{report.id}/download?format=pdf&advanced_export=true")
    assert resp.status_code == 402
    assert resp.json()["detail"]["feature"] == "report_export"
