from fastapi.testclient import TestClient

from backend.app import app


def test_summary_endpoint_works():
    client = TestClient(app)
    res = client.get("/summary")
    assert res.status_code == 200
    body = res.json()
    assert "kunden" in body
    assert "touren" in body
