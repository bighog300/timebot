import uuid
from app.models.admin_audit import AdminAuditEvent

def test_non_admin_cannot_access_provider_endpoints(client,test_user,db):
    test_user.role='viewer'; db.commit()
    assert client.get('/api/v1/admin/email/providers').status_code==403

def test_provider_config_safe_and_patch_behaviors(client,test_user,db):
    test_user.role='admin'; db.commit()
    r=client.patch('/api/v1/admin/email/providers/resend',json={'from_email':'noreply@example.com','api_key':'secret-abc'})
    assert r.status_code==200
    payload=r.json(); assert payload['configured'] is True; assert 'api_key' not in str(payload); assert 'encrypted' not in str(payload)
    r2=client.patch('/api/v1/admin/email/providers/resend',json={'enabled':True})
    assert r2.status_code==200 and r2.json()['configured'] is True
    r3=client.patch('/api/v1/admin/email/providers/resend',json={'api_key':''})
    assert r3.status_code==200 and r3.json()['configured'] is False
    ev=db.query(AdminAuditEvent).filter(AdminAuditEvent.entity_type=='email_provider_config').first(); assert ev is not None; assert 'secret-abc' not in str(ev.details)

def test_template_crud_and_archive_rules(client,test_user,db):
    test_user.role='admin'; db.commit()
    body={'name':'Welcome','slug':'welcome','category':'transactional','status':'draft','subject':'Hello','html_body':'<p>Hi</p>','variables_json':{'name':'string'}}
    c=client.post('/api/v1/admin/email/templates',json=body); assert c.status_code==201
    tid=c.json()['id']
    dup=client.post('/api/v1/admin/email/templates',json=body); assert dup.status_code==400
    u=client.patch(f'/api/v1/admin/email/templates/{tid}',json={'subject':'Hello 2','status':'active'}); assert u.status_code==200
    d=client.delete(f'/api/v1/admin/email/templates/{tid}'); assert d.status_code==200 and d.json()['status']=='archived'
    blocked=client.patch(f'/api/v1/admin/email/templates/{tid}',json={'subject':'Nope'}); assert blocked.status_code==400
    restore=client.patch(f'/api/v1/admin/email/templates/{tid}',json={'status':'draft'}); assert restore.status_code==200
    evs=db.query(AdminAuditEvent).filter(AdminAuditEvent.entity_type=='email_template').all(); assert len(evs)>=3
