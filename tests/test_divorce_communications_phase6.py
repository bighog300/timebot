from app.models.document import Document


def _mk_doc(db, ws_id, user_id, subj='Settlement offer', text='Please respond by 2026-05-20. I offer $500 monthly support. I allege missed payments.'):
    d = Document(filename='Email', original_path='gmail://1', file_type='txt', file_size=100, mime_type='text/plain', source='gmail', source_id='msg-1', user_id=user_id, workspace_id=ws_id, raw_text=text, extracted_metadata={'sender':'spouse@example.com','recipients':['me@example.com'],'subject':subj,'received_at':'2026-05-01','gmail_message_id':'msg-1'})
    db.add(d); db.commit(); return d


def test_divorce_communications_extract_and_crud_and_access(client, db, test_user):
    ws1 = client.post('/api/v1/divorce/setup', json={"case_title":"Case","jurisdiction":"CA","current_stage":"filed","children_involved":True,"financial_disclosure_started":False,"lawyer_involved":True}).json()
    ws2 = client.post('/api/v1/divorce/setup', json={"case_title":"Case2","jurisdiction":"CA","current_stage":"filed","children_involved":False,"financial_disclosure_started":False,"lawyer_involved":False}).json()
    _mk_doc(db, ws1['id'], test_user.id)
    r1 = client.post(f"/api/v1/divorce/communications/extract/{ws1['id']}")
    assert r1.status_code == 200 and r1.json()['created_count'] >= 1
    r2 = client.post(f"/api/v1/divorce/communications/extract/{ws1['id']}")
    assert r2.json()['created_count'] == 0
    rows = client.get(f"/api/v1/divorce/communications/{ws1['id']}").json(); assert len(rows) >= 1
    cid = rows[0]['id']
    assert rows[0]['extracted_deadlines_json']
    assert client.post(f'/api/v1/divorce/communications/{cid}/accept').status_code == 200
    assert client.post(f'/api/v1/divorce/communications/{cid}/reject').status_code == 200
    assert client.patch(f'/api/v1/divorce/communications/{cid}', json={'tone':'neutral'}).status_code == 200
    assert client.delete(f'/api/v1/divorce/communications/{cid}').status_code == 200
    assert client.get(f"/api/v1/divorce/communications/{ws2['id']}").status_code == 200


def test_divorce_dashboard_includes_communication_metrics(client, db, test_user):
    ws = client.post('/api/v1/divorce/setup', json={"case_title":"Case","jurisdiction":"CA","current_stage":"filed","children_involved":True,"financial_disclosure_started":False,"lawyer_involved":True}).json()
    _mk_doc(db, ws['id'], test_user.id, subj='Urgent court update', text='Urgent: court hearing deadline tomorrow')
    client.post(f"/api/v1/divorce/communications/extract/{ws['id']}")
    dash = client.get(f"/api/v1/divorce/dashboard/{ws['id']}").json()
    assert dash['communication_count'] >= 1
    assert 'hostile_or_urgent_count' in dash and 'recent_communications' in dash
