from fastapi.testclient import TestClient

from sdpremote.app import app


def test_index_200():
    client = TestClient(app)
    resp = client.get('/')
    assert resp.status_code == 200
