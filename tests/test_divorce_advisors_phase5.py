from fastapi.testclient import TestClient


def test_divorce_advisors_mapping(client: TestClient, auth_headers):
    res = client.get('/api/v1/chat/assistants', headers=auth_headers)
    assert res.status_code == 200
    out = client.get('/api/v1/divorce/advisors', headers=auth_headers)
    assert out.status_code == 200
    data = out.json()
    keys = {row['key'] for row in data}
    assert {'legal_advisor','psychology_advisor','document_analyst','general_divorce_advisor'}.issubset(keys)
    legal = next(row for row in data if row['key']=='legal_advisor')
    assert legal['assistant_name'] == 'South African Legal Defense Expert'
    assert legal['locked'] is True
