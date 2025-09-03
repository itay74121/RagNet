import json
import pytest
from fastapi.testclient import TestClient

from RagFileManager.api.api import app


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_login_endpoint_returns_cookie_and_token(client):
    payload = {"username": "alice", "password": "secret", "user_id": {
        "username":"alice",
        "user_id": "123456"
    }}
    resp = client.post("/api/v1/auth/login", json=payload)
    assert resp.status_code == 200 or resp.status_code == 201
    # Token should be returned via cookie or header
    assert resp.cookies.get("auth_token") is not None or resp.headers.get("authorization") is not None


