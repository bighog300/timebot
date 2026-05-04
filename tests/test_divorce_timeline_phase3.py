from app.models.document import Document


def _mk_doc(db, ws_id, user_id, text):
    d = Document(filename='d.txt', original_path='/tmp/d.txt', file_type='txt', file_size=1, mime_type='text/plain', processing_status='completed', source='upload', user_id=user_id, workspace_id=ws_id, raw_text=text)
    db.add(d); db.commit(); db.refresh(d)
    return d


def test_divorce_timeline_extract_dedupe_and_crud(client, db, test_user):
    ws = client.post('/api/v1/divorce/setup', json={"case_title":"Case","jurisdiction":"CA","current_stage":"filed","children_involved":True,"financial_disclosure_started":False,"lawyer_involved":True}).json()
    _mk_doc(db, ws['id'], test_user.id, 'On 2026-01-10 court hearing was scheduled. payment sent 01/15/2026')
    ex1 = client.post(f"/api/v1/divorce/timeline/extract/{ws['id']}")
    assert ex1.status_code == 200 and ex1.json()['created_count'] > 0
    ex2 = client.post(f"/api/v1/divorce/timeline/extract/{ws['id']}")
    assert ex2.status_code == 200
    events = client.get(f"/api/v1/divorce/timeline/{ws['id']}").json()
    assert len(events) == ex1.json()['created_count']
    eid = events[0]['id']
    assert client.post(f'/api/v1/divorce/timeline/{eid}/accept').status_code == 200
    assert client.patch(f'/api/v1/divorce/timeline/{eid}', json={'title': 'Updated title', 'category': 'legal'}).status_code == 200
    assert client.post(f'/api/v1/divorce/timeline/{eid}/reject').status_code == 200
    assert client.delete(f'/api/v1/divorce/timeline/{eid}').status_code == 200


def test_divorce_timeline_workspace_access_and_dashboard(client, db, test_user):
    ws1 = client.post('/api/v1/divorce/setup', json={"case_title":"Case","jurisdiction":"CA","current_stage":"filed","children_involved":True,"financial_disclosure_started":False,"lawyer_involved":True}).json()
    ws2 = client.post('/api/v1/divorce/setup', json={"case_title":"Other","jurisdiction":"CA","current_stage":"filed","children_involved":False,"financial_disclosure_started":False,"lawyer_involved":False}).json()
    from app.models.workspace import WorkspaceMember
    db.query(WorkspaceMember).filter_by(workspace_id=ws2['id'], user_id=test_user.id).delete()
    db.commit()
    assert client.get(f"/api/v1/divorce/timeline/{ws2['id']}").status_code == 403
    _mk_doc(db, ws1['id'], test_user.id, 'Filed on 2026-02-01')
    client.post(f"/api/v1/divorce/timeline/extract/{ws1['id']}")
    dash = client.get(f"/api/v1/divorce/dashboard/{ws1['id']}").json()
    assert 'suggested_timeline_count' in dash and 'high_confidence_event_count' in dash
