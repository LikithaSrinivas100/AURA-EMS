"""TC_F3: replay next/reset + invalid zone."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_replay_reset_and_next():
    r = client.post("/replay/reset", params={"zone": "campus"})
    assert r.status_code == 200
    assert r.json()["cursor"] == 0
    n = client.get("/replay/next", params={"cursor": 0, "n": 4, "zone": "campus"})
    assert n.status_code == 200
    body = n.json()
    assert body["next_cursor"] == 4
    assert len(body["items"]) == 4
    assert "peak_alerts" in body


def test_replay_invalid_zone():
    assert client.get("/replay/next", params={"zone": "labs"}).status_code == 422
