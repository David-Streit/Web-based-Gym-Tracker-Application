from fastapi.testclient import TestClient
from api.main import app


def test_health():
    # Startup is not required for this route: it does not access the database.
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_workouts_require_authentication():
    response = TestClient(app).get("/api/workouts")
    assert response.status_code == 401
