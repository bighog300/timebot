from app.models.prompt_template import PromptTemplate


def test_get_session_flattened_shape(client, db, test_user):
    s = client.post('/api/v1/chat/sessions', json={'title': 'x'}).json()
    r = client.get(f"/api/v1/chat/sessions/{s['id']}")
    assert r.status_code == 200
    body = r.json()
    assert 'id' in body and 'messages' in body and 'linked_document_ids' in body
    assert 'session' not in body


def test_chat_prompt_templates_endpoint(client, db, test_user):
    t = PromptTemplate(type='chat', name='General chat template', content='be helpful', version=1, enabled=True)
    db.add(t)
    db.commit()
    r = client.get('/api/v1/chat/prompt-templates')
    assert r.status_code == 200
    body = r.json()
    assert any(item['id'] == str(t.id) for item in body)
