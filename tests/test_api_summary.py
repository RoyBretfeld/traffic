from fastapi.testclient import TestClient

from backend.app import create_app
app = create_app()


def test_summary_endpoint_works():
    client = TestClient(app)
    res = client.get("/summary")
    assert res.status_code == 200
    body = res.json()
    assert "kunden" in body
    assert "touren" in body
