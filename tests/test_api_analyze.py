from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_analyze_valid_request():
    response = client.post(
        "/analyze",
        json={"idea": "Should I build an AI study assistant for college students?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "report" in data
    assert "meta" in data
    assert data["report"]["engine"] == "mock"
    assert data["meta"]["duration_ms"] >= 0


def test_analyze_idea_too_short():
    response = client.post("/analyze", json={"idea": "hi"})
    assert response.status_code == 422


def test_analyze_empty_body():
    response = client.post("/analyze", json={})
    assert response.status_code == 422
