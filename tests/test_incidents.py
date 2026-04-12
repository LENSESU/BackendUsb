"""Tests del endpoint GET /api/v1/incidents/."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

EXPECTED_FIELDS = {"id", "title", "category", "status", "priority", "location", "reported_by", "created_at"}

VALID_STATUSES = {"open", "in_progress", "resolved", "closed"}
VALID_PRIORITIES = {"low", "medium", "high", "critical"}
VALID_CATEGORIES = {"hardware", "software", "network", "security", "other"}


def test_list_incidents_returns_200():
    response = client.get("/api/v1/incidents/")
    assert response.status_code == 200


def test_list_incidents_returns_list():
    response = client.get("/api/v1/incidents/")
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_list_incidents_fields():
    response = client.get("/api/v1/incidents/")
    incident = response.json()[0]
    assert EXPECTED_FIELDS == set(incident.keys())


def test_list_incidents_valid_enums():
    response = client.get("/api/v1/incidents/")
    for incident in response.json():
        assert incident["status"] in VALID_STATUSES
        assert incident["priority"] in VALID_PRIORITIES
        assert incident["category"] in VALID_CATEGORIES


def test_list_incidents_ordered_by_date_desc():
    response = client.get("/api/v1/incidents/")
    dates = [i["created_at"] for i in response.json()]
    assert dates == sorted(dates, reverse=True)
