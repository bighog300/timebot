import uuid

from app.models.prompt_template import PromptTemplate
from app.services.prompt_templates import activate_prompt_template, get_active_prompt_content


def test_admin_can_create_prompt_template(client, test_user, db):
    test_user.role = "admin"
    db.commit()
    r = client.post("/api/v1/admin/prompts", json={"type": "chat", "name": "v1", "content": "You are custom.", "version": 1, "is_active": False})
    assert r.status_code == 201
    body = r.json()
    assert body["type"] == "chat"
    assert body["name"] == "v1"


def test_non_admin_cannot_create_or_update_prompts(client, test_user, db):
    test_user.role = "viewer"
    db.commit()
    create = client.post("/api/v1/admin/prompts", json={"type": "chat", "name": "v1", "content": "X", "version": 1, "is_active": False})
    assert create.status_code == 403

    seeded = PromptTemplate(type="chat", name="seed", content="seed", version=1, is_active=False)
    db.add(seeded)
    db.commit()
    update = client.put(f"/api/v1/admin/prompts/{seeded.id}", json={"content": "changed"})
    assert update.status_code == 403


def test_active_prompt_loaded_by_type_and_fallback(db):
    assert get_active_prompt_content(db, "report", "default report") == "default report"
    template = PromptTemplate(type="report", name="custom", content="custom report", version=2, is_active=True)
    db.add(template)
    db.commit()
    assert get_active_prompt_content(db, "report", "default report") == "custom report"


def test_activating_prompt_deactivates_others_same_type(db):
    p1 = PromptTemplate(type="retrieval", name="v1", content="one", version=1, is_active=True)
    p2 = PromptTemplate(type="retrieval", name="v2", content="two", version=2, is_active=False)
    db.add_all([p1, p2])
    db.commit()
    activate_prompt_template(db, p2)
    db.commit()
    db.refresh(p1)
    db.refresh(p2)
    assert p1.is_active is False
    assert p2.is_active is True


def test_chat_uses_fallback_prompt_when_none_configured(client, monkeypatch, db):
    from app.models.document import Document
    from app.models.user import User

    user = db.query(User).first()
    doc = Document(
        id=uuid.uuid4(), filename="alpha.txt", original_path="/tmp/alpha.txt", file_type="txt", file_size=10,
        mime_type="text/plain", processing_status="completed", source="upload", summary="Alpha summary", entities={}, action_items=[], key_points=[], ai_tags=[], user_id=user.id
    )
    db.add(doc)
    db.commit()

    captured = {}

    class DummyChoice:
        message = type("M", (), {"content": "ok"})

    class DummyResp:
        choices = [DummyChoice()]

    class DummyComp:
        def create(self, **kwargs):
            captured["system_prompt"] = kwargs["messages"][0]["content"]
            return DummyResp()

    class DummyChat:
        completions = DummyComp()

    monkeypatch.setattr("app.config.settings.OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.api.v1.chat.openai_client_service._client", type("C", (), {"chat": DummyChat()})())

    s = client.post("/api/v1/chat/sessions", json={"title": "s"}).json()
    r = client.post(f"/api/v1/chat/sessions/{s['id']}/messages", json={"message": "alpha"})
    assert r.status_code == 200
    assert captured["system_prompt"].startswith("You are Timebot")
