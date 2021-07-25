from base64 import b64encode

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from sdpremote.user import user


@pytest.fixture(scope='module')
def app() -> FastAPI:
    app = FastAPI()

    def user_check(login: str = Depends(user)):
        return login

    app.get('/')(user_check)
    app.get('/{user}')(user_check)

    return app


@pytest.fixture(scope='module')
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


@pytest.fixture(scope='module')
def headers() -> dict[str, str]:
    value = b64encode(b'user:pass').decode()
    return {'Authorization': f'Basic {value}'}


def test_extract_user_from_header(client: TestClient, headers: dict[str, str]):
    resp = client.get('/', headers=headers)
    assert resp.status_code == 200
    assert 'user' in resp.text


def test_401_when_invalid_header(client: TestClient):
    resp = client.get('/')
    assert resp.status_code == 401

    resp = client.get('/', headers={'Authorization': 'Digest blabla'})
    assert resp.status_code == 401

    resp = client.get('/', headers={'Authorization': 'Basic blabla'})
    assert resp.status_code == 401


def test_match_user_and_path(client: TestClient, headers: dict[str, str]):
    resp = client.get('/user', headers=headers)
    assert resp.status_code == 200
    assert 'user' in resp.text


def test_mismatch_user_and_path(client: TestClient, headers: dict[str, str]):
    resp = client.get('/another', headers=headers)
    assert resp.status_code == 403
