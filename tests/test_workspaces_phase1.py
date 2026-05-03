from app.models.workspace import Workspace


def test_register_creates_personal_workspace(client):
    r = client.post('/api/v1/auth/register', json={'email':'ws1@example.com','display_name':'Ws1','password':'Password123!@#'})
    assert r.status_code == 201
    token = r.json()['access_token']
    me = client.get('/api/v1/workspaces', headers={'Authorization': f'Bearer {token}'})
    assert me.status_code == 200
    items = me.json()
    assert len(items) >= 1
    assert any(w['type'] == 'personal' for w in items)
