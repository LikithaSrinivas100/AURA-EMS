"""TC_F6: recommended_action on peaks + HIGH present."""
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import RECOMMENDED_ACTIONS

client = TestClient(app)


def test_peaks_include_recommended_action():
    r = client.get("/forecasts/peaks", params={"limit": 10, "zone": "campus"})
    assert r.status_code == 200
    items = r.json()["items"]
    assert items
    for it in items:
        assert it["recommended_action"] == RECOMMENDED_ACTIONS[it["risk_level"]]
