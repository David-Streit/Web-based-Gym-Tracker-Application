
from fastapi.testclient import TestClient

from api.main import app


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_workouts_require_authentication():
    with TestClient(app) as client:
        response = client.get("/api/workouts")

    assert response.status_code == 401
