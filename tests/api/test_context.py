from fastapi.testclient import TestClient
import pytest

from RagFileManager.api.api import app


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_context_query_requires_auth(client):
    resp = client.get("/api/v1/context/query", params={"q": "test", "top_k": 3})
    assert resp.status_code in (401, 403)
