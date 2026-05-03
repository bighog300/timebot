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


def test_admin_cannot_create_prompt_template_with_whitespace_only_content(client, test_user, db):
    test_user.role = "admin"
    db.commit()

    r = client.post("/api/v1/admin/prompts", json={"type": "chat", "name": "v1", "content": "   \n\t  ", "version": 1, "is_active": False})
    assert r.status_code == 422
    assert "non-whitespace character" in str(r.json())


def test_admin_cannot_update_prompt_template_with_whitespace_only_content(client, test_user, db):
    test_user.role = "admin"
    seeded = PromptTemplate(type="chat", name="seed", content="seed", version=1, is_active=False)
    db.add(seeded)
    db.commit()

    r = client.put(f"/api/v1/admin/prompts/{seeded.id}", json={"content": "\n \t "})
    assert r.status_code == 422
    assert "non-whitespace character" in str(r.json())


def test_active_prompt_loaded_by_type_and_fallback(db):
    assert get_active_prompt_content(db, "report", "default report") == "default report"
    template = PromptTemplate(type="report", name="custom", content="custom report", version=2, is_active=True)
    db.add(template)
    db.commit()
    assert get_active_prompt_content(db, "report", "default report") == "custom report"



def test_blank_active_prompt_falls_back_to_default(db):
    template = PromptTemplate(type="report", name="blank", content="   ", version=1, is_active=True)
    db.add(template)
    db.commit()
    assert get_active_prompt_content(db, "report", "default report") == "default report"

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


def test_admin_can_test_prompt_template(client, test_user, db, monkeypatch):
    test_user.role = "admin"
    db.commit()

    class DummyChoice:
        message = type("M", (), {"content": "preview output"})

    class DummyResp:
        choices = [DummyChoice()]

    class DummyComp:
        def create(self, **kwargs):
            return DummyResp()

    class DummyChat:
        completions = DummyComp()

    monkeypatch.setattr("app.config.settings.OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.api.v1.admin.openai_client_service._client", type("C", (), {"chat": DummyChat()})())

    r = client.post("/api/v1/admin/prompts/test", json={"type": "chat", "content": "You are helper", "sample_context": "Question: hello"})
    assert r.status_code == 200
    assert r.json()["preview"] == "preview output"


def test_non_admin_cannot_test_prompt_template(client, test_user, db):
    test_user.role = "viewer"
    db.commit()
    r = client.post("/api/v1/admin/prompts/test", json={"type": "chat", "content": "x", "sample_context": "y"})
    assert r.status_code == 403


def test_admin_prompt_test_validation_error_shape(client, test_user, db):
    test_user.role = "admin"
    db.commit()
    r = client.post("/api/v1/admin/prompts/test", json={"prompt_type": "chat", "prompt_content": "", "sample_context": ""})
    assert r.status_code == 422
    detail = r.json()["detail"]
    assert isinstance(detail, list)
    assert any(item.get("loc", [None])[-1] == "type" for item in detail)


def test_prompt_test_does_not_persist_or_activate(client, test_user, db, monkeypatch):
    test_user.role = "admin"
    existing = PromptTemplate(type="chat", name="seed", content="seed", version=1, is_active=True)
    db.add(existing)
    db.commit()

    class DummyChoice:
        message = type("M", (), {"content": "preview output"})

    class DummyResp:
        choices = [DummyChoice()]

    class DummyComp:
        def create(self, **kwargs):
            return DummyResp()

    class DummyChat:
        completions = DummyComp()

    monkeypatch.setattr("app.config.settings.OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.api.v1.admin.openai_client_service._client", type("C", (), {"chat": DummyChat()})())

    before_count = db.query(PromptTemplate).count()
    r = client.post("/api/v1/admin/prompts/test", json={"type": "chat", "content": "new content", "sample_context": "ctx"})
    assert r.status_code == 200

    after_count = db.query(PromptTemplate).count()
    db.refresh(existing)
    assert before_count == after_count
    assert existing.is_active is True
    assert existing.content == "seed"


def test_seed_default_prompt_templates_fresh_db_creates_all_types(db):
    from app.services.prompt_templates import seed_default_prompt_templates

    created = seed_default_prompt_templates(db)
    assert created == 5
    types = {row.type for row in db.query(PromptTemplate).all()}
    assert types == {"chat", "retrieval", "report", "timeline_extraction", "relationship_detection"}


def test_seed_default_prompt_templates_is_idempotent(db):
    from app.services.prompt_templates import seed_default_prompt_templates

    assert seed_default_prompt_templates(db) == 5
    before_count = db.query(PromptTemplate).count()
    assert seed_default_prompt_templates(db) == 0
    assert db.query(PromptTemplate).count() == before_count


def test_seed_default_prompt_templates_does_not_overwrite_existing(db):
    from app.services.prompt_templates import seed_default_prompt_templates

    existing = PromptTemplate(type="chat", name="edited", content="custom", version=7, is_active=True)
    db.add(existing)
    db.commit()

    created = seed_default_prompt_templates(db)
    assert created == 4
    db.refresh(existing)
    assert existing.name == "edited"
    assert existing.content == "custom"
    assert existing.version == 7


def test_seeded_templates_are_editable_via_admin_api(client, test_user, db):
    from app.services.prompt_templates import seed_default_prompt_templates

    test_user.role = "admin"
    db.commit()
    seed_default_prompt_templates(db)
    prompt = db.query(PromptTemplate).filter(PromptTemplate.type == "retrieval").first()

    r = client.put(f"/api/v1/admin/prompts/{prompt.id}", json={"content": "Edited retrieval template", "is_active": True})
    assert r.status_code == 200
    assert r.json()["content"] == "Edited retrieval template"


def test_runtime_falls_back_when_seeded_template_disabled(db):
    from app.services.prompt_templates import seed_default_prompt_templates

    seed_default_prompt_templates(db)
    template = db.query(PromptTemplate).filter(PromptTemplate.type == "report").first()
    template.is_active = False
    db.add(template)
    db.commit()

    assert get_active_prompt_content(db, "report", "built-in report") == "built-in report"

def test_create_default_clears_previous_default_for_same_purpose(client, test_user, db):
    test_user.role = 'admin'
    existing = PromptTemplate(type='chat', name='existing', content='one', version=1, is_default=True)
    db.add(existing)
    db.commit()

    r = client.post('/api/v1/admin/prompts', json={'type': 'chat', 'name': 'new', 'content': 'two', 'version': 2, 'is_default': True})
    assert r.status_code == 201

    db.refresh(existing)
    assert existing.is_default is False
    created = db.query(PromptTemplate).filter(PromptTemplate.id == r.json()['id']).first()
    assert created is not None
    assert created.is_default is True


def test_update_to_default_clears_previous_default_for_same_purpose(client, test_user, db):
    test_user.role = 'admin'
    p1 = PromptTemplate(type='report', name='d1', content='one', version=1, is_default=True)
    p2 = PromptTemplate(type='report', name='d2', content='two', version=2, is_default=False)
    db.add_all([p1, p2])
    db.commit()

    r = client.put(f'/api/v1/admin/prompts/{p2.id}', json={'is_default': True})
    assert r.status_code == 200

    db.refresh(p1)
    db.refresh(p2)
    assert p1.is_default is False
    assert p2.is_default is True


def test_different_purposes_can_each_have_default(client, test_user, db):
    test_user.role = 'admin'
    db.commit()

    r1 = client.post('/api/v1/admin/prompts', json={'type': 'chat', 'name': 'chat default', 'content': 'chat', 'version': 1, 'is_default': True})
    r2 = client.post('/api/v1/admin/prompts', json={'type': 'report', 'name': 'report default', 'content': 'report', 'version': 1, 'is_default': True})
    assert r1.status_code == 201
    assert r2.status_code == 201

    chat_defaults = db.query(PromptTemplate).filter(PromptTemplate.type == 'chat', PromptTemplate.is_default.is_(True)).count()
    report_defaults = db.query(PromptTemplate).filter(PromptTemplate.type == 'report', PromptTemplate.is_default.is_(True)).count()
    assert chat_defaults == 1
    assert report_defaults == 1


def test_admin_create_prompt_with_fallback_fields(client, test_user, db):
    test_user.role = "admin"
    db.commit()
    r = client.post("/api/v1/admin/prompts", json={"type":"chat","name":"fb","content":"c","version":1,"provider":"openai","model":"gpt-4o-mini","fallback_enabled":True,"fallback_provider":"gemini","fallback_model":"gemini-1.5-flash"})
    assert r.status_code == 201
    assert r.json()["fallback_enabled"] is True


def test_admin_create_prompt_invalid_fallback_model_fails(client, test_user, db):
    test_user.role = "admin"
    db.commit()
    r = client.post("/api/v1/admin/prompts", json={"type":"chat","name":"fb","content":"c","version":1,"provider":"openai","model":"gpt-4o-mini","fallback_enabled":True,"fallback_provider":"gemini","fallback_model":"bad-model"})
    assert r.status_code == 422


def test_prompt_test_uses_fallback_on_primary_failure(client, test_user, db, monkeypatch):
    test_user.role = "admin"
    db.commit()
    monkeypatch.setattr("app.config.settings.OPENAI_API_KEY", "test-key")
    calls = []

    def fake(provider, payload):
        calls.append(provider)
        if provider == "openai":
            from app.services.openai_client import APIError
            raise APIError("primary fail")
        return type("R", (), {"choices": [type("C", (), {"message": type("M", (), {"content": "ok via fallback"})()})()]})()

    monkeypatch.setattr("app.api.v1.admin.openai_client_service.generate_completion_for_provider", fake)
    r = client.post('/api/v1/admin/prompts/test', json={"type": "chat", "content": "x", "sample_context": "y", "provider": "openai", "model": "gpt-4o-mini", "fallback_enabled": True, "fallback_provider": "gemini", "fallback_model": "gemini-1.5-flash"})
    assert r.status_code == 200
    assert r.json()["fallback_used"] is True
    assert calls == ["openai", "gemini"]


def test_prompt_test_primary_failure_without_fallback_returns_error(client, test_user, db, monkeypatch):
    test_user.role = "admin"
    db.commit()
    monkeypatch.setattr("app.config.settings.OPENAI_API_KEY", "test-key")
    from app.services.openai_client import APIError
    monkeypatch.setattr("app.api.v1.admin.openai_client_service.generate_completion_for_provider", lambda *_: (_ for _ in ()).throw(APIError("boom")))
    r = client.post('/api/v1/admin/prompts/test', json={"type":"chat","content":"x","sample_context":"y","provider":"openai","model":"gpt-4o-mini"})
    assert r.status_code == 502

