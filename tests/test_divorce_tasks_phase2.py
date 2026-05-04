import uuid
from app.models.document import Document
from app.models.workspace import WorkspaceMember
from app.models.user import User


def _mk_doc(db, user, ws_id, text):
    d=Document(id=uuid.uuid4(), filename='a.txt', original_path='/tmp/a.txt', file_type='txt', file_size=1, mime_type='text/plain', processing_status='completed', source='upload', raw_text=text, action_items=['Submit financial disclosure'], user_id=user.id, workspace_id=ws_id)
    db.add(d); db.commit(); db.refresh(d); return d


def test_divorce_task_extract_accept_reject_and_dashboard(client, db, test_user):
    ws = client.post('/api/v1/divorce/setup', json={"case_title":"Case","jurisdiction":"CA","current_stage":"filed","children_involved":True,"financial_disclosure_started":False,"lawyer_involved":True}).json()
    _mk_doc(db, test_user, ws['id'], 'Urgent: respond before deadline to court notice')
    ex = client.post(f"/api/v1/divorce/tasks/extract/{ws['id']}")
    assert ex.status_code == 200 and ex.json()['created_count'] >= 1
    tasks = client.get(f"/api/v1/divorce/tasks/{ws['id']}").json()
    tid = tasks[0]['id']
    assert client.post(f'/api/v1/divorce/tasks/{tid}/accept').status_code == 200
    assert client.patch(f'/api/v1/divorce/tasks/{tid}', json={'status':'in_progress','priority':'high'}).status_code == 200
    assert client.post(f'/api/v1/divorce/tasks/{tid}/reject').status_code == 200
    dash = client.get(f"/api/v1/divorce/dashboard/{ws['id']}")
    assert dash.status_code == 200
    assert 'suggested_task_count' in dash.json()


def test_divorce_task_access_control(client, db, test_user):
    ws = client.post('/api/v1/divorce/setup', json={"case_title":"Case","jurisdiction":"CA","current_stage":"filed","children_involved":True,"financial_disclosure_started":False,"lawyer_involved":True}).json()
    other = User(id=uuid.uuid4(), email='other@example.com', password_hash='x', display_name='Other', is_active=True, role='editor')
    db.add(other); db.commit()
    other_ws = client.post('/api/v1/divorce/setup', json={"case_title":"Other","jurisdiction":"CA","current_stage":"filed","children_involved":False,"financial_disclosure_started":False,"lawyer_involved":False}).json()
    db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == other_ws['id'], WorkspaceMember.user_id == test_user.id).delete(); db.commit()
    assert client.get(f"/api/v1/divorce/tasks/{other_ws['id']}").status_code == 403
