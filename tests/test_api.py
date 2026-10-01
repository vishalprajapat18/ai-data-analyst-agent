"""The HTTP contract: does the API accept and reject the right requests?

These never call the model. Asking a real question takes minutes and costs tokens —
that is what the LangSmith evaluation is for.
"""

from fastapi.testclient import TestClient

from app.api.main import app

client = TestClient(app)


def test_health_reports_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_a_missing_message_is_rejected_before_the_agent_runs():
    response = client.post("/ask", json={})
    assert response.status_code == 422


def test_a_too_short_message_is_rejected():
    response = client.post("/ask", json={"message": "a"})
    assert response.status_code == 422