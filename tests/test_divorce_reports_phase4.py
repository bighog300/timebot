import uuid
from app.models.document import Document
from app.models.divorce import DivorceTimelineItem
from app.models.intelligence import DocumentActionItem
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember


def _ws(db, user):
    ws=Workspace(name='Case', type='team', workspace_type='divorce_case', owner_user_id=user.id)
    db.add(ws); db.flush(); db.add(WorkspaceMember(workspace_id=ws.id,user_id=user.id,role='owner')); db.commit(); return ws


def _doc(db,user,ws):
    d=Document(filename='a.txt',original_path='/tmp/a.txt',file_type='txt',file_size=1,mime_type='text/plain',processing_status='completed',source='upload',user_id=user.id,workspace_id=ws.id,summary='Doc summary')
    db.add(d); db.commit(); db.refresh(d); return d


def test_generate_case_overview_and_refs(client,db,test_user):
    ws=_ws(db,test_user); d=_doc(db,test_user,ws)
    t=DocumentActionItem(document_id=d.id,workspace_id=ws.id,content='File disclosure',status='open')
    rj=DocumentActionItem(document_id=d.id,workspace_id=ws.id,content='Rejected',status='rejected')
    ev=DivorceTimelineItem(workspace_id=ws.id,title='Hearing scheduled',category='legal',review_status='accepted',source_document_id=d.id)
    ev2=DivorceTimelineItem(workspace_id=ws.id,title='Ignore me',category='legal',review_status='rejected',source_document_id=d.id)
    db.add_all([t,rj,ev,ev2]); db.commit()
    resp=client.post(f'/api/v1/divorce/reports/{ws.id}/generate',json={'report_type':'case_overview_report'})
    assert resp.status_code==200
    payload=resp.json(); assert str(ev.id) in payload['source_timeline_item_ids_json']; assert str(ev2.id) not in payload['source_timeline_item_ids_json']


def test_generate_lawyer_handoff_pack_pro_only(client,db,test_user,grant_pro_subscription):
    ws=_ws(db,test_user); grant_pro_subscription(test_user.id)
    resp=client.post(f'/api/v1/divorce/reports/{ws.id}/generate',json={'report_type':'lawyer_handoff_pack'})
    assert resp.status_code==200
    assert 'Matter Summary' in resp.json()['content_markdown']


def test_free_user_blocked_for_pro_report(client,db,test_user):
    ws=_ws(db,test_user)
    resp=client.post(f'/api/v1/divorce/reports/{ws.id}/generate',json={'report_type':'lawyer_handoff_pack'})
    assert resp.status_code==402


def test_access_control_blocks_other_user(client,db,test_user):
    ws=_ws(db,test_user)
    other=User(id=uuid.uuid4(),email='o@example.com',password_hash='x',display_name='o',is_active=True,role='editor'); db.add(other); db.commit()
    resp=client.post(f'/api/v1/divorce/reports/{ws.id}/generate',json={'report_type':'case_overview_report'})
    assert resp.status_code==200
    rid=resp.json()['id']
    from app.api.deps import get_current_user
    client.app.dependency_overrides[get_current_user]=lambda: other
    assert client.get(f'/api/v1/divorce/reports/detail/{rid}').status_code==403


def test_dashboard_report_metrics_update(client,db,test_user):
    ws=_ws(db,test_user)
    client.post(f'/api/v1/divorce/reports/{ws.id}/generate',json={'report_type':'case_overview_report'})
    dash=client.get(f'/api/v1/divorce/dashboard/{ws.id}').json()
    assert dash['report_count']>=1
