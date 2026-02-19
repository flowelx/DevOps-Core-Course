from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert "service" in data
    assert data["service"]["name"] == "devops-info-request"

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_404_error():
    response = client.get("/not-exists")
    assert response.status_code == 404