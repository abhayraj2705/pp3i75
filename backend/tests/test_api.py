from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/api/health").json() == {"status": "ok"}


def test_day_ahead_returns_full_day():
    body = client.get("/api/day-ahead", params={"date": "2026-01-15", "cutoff_hour": 10}).json()
    assert len(body["points"]) == 24
    assert body["cutoff"] == "2026-01-14T10:00:00+00:00"
    assert body["forecast_published"] <= body["cutoff"]
    assert body["summary"]["count"] == 24
    assert all(p["band_low"] <= p["forecast"] <= p["band_high"] for p in body["points"])


def test_day_ahead_rejects_date_outside_range():
    response = client.get("/api/day-ahead", params={"date": "2026-03-01"})
    assert response.status_code == 400


def test_day_ahead_rejects_bad_input():
    assert client.get("/api/day-ahead", params={"date": "not-a-date"}).status_code == 422
    assert client.get("/api/day-ahead", params={"date": "2026-01-15", "cutoff_hour": 24}).status_code == 422


def test_accuracy_shape():
    body = client.get("/api/accuracy").json()
    assert body["summary"]["count"] == 31 * 24
    assert len(body["by_hour"]) == 24
    assert len(body["daily"]) == 31
    assert len(body["by_horizon"]) == 8
