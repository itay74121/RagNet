from fastapi.testclient import TestClient
import pytest

from RagFileManager.api.api import app
from RagFileManager.api.controller.rag import RagQuery


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_context_authorized_calls_rag(monkeypatch, client):
    # login to set cookie
    payload = {"username": "alice", "password": "secret", "user_id": {
        "username":"itay","user_id":"123456"
    }}
    resp = client.post("/api/v1/auth/login", json=payload)
    # Mock RagQuery.query to avoid external API calls
    monkeypatch.setattr(RagQuery, "query", lambda self, q, top_k=5: {"documents": ["doc1"], "metadatas": [{}]})
    resp = client.get("/api/v1/context/query", params={"q": "test", "top_k": 2})
    assert resp.status_code == 200
    data = resp.json()
    assert "documents" in data
