from app.models.email import EmailProviderConfig, EmailSuppression, EmailCampaignRecipient

def test_non_admin_blocked(client):
    assert client.get('/api/v1/admin/email/suppressions').status_code == 403

def test_suppression_crud_and_send_controls(client, admin_token_headers, db, monkeypatch):
    h = admin_token_headers()
    r=client.post('/api/v1/admin/email/suppressions', headers=h, json={'email':'X@Example.com','reason':'manual'})
    assert r.status_code==201 and r.json()['email']=='x@example.com'
    assert client.get('/api/v1/admin/email/suppressions', headers=h).status_code==200
    assert client.delete('/api/v1/admin/email/suppressions/x@example.com', headers=h).status_code==200
