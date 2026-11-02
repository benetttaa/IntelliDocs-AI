from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["app"] == "IntelliDocs AI"


def test_upload_and_query_round_trip() -> None:
    content = b"Remote work policy allows hybrid work for up to three days per week with manager approval.\nThe onboarding guide explains the benefits and required equipment checkouts."
    response = client.post(
        "/api/documents/upload",
        files=[("files", ("policy.txt", content, "text/plain"))],
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["chunk_count"] > 0

    chat_response = client.post(
        "/api/chat",
        json={"question": "What is the remote work policy?", "top_k": 3},
    )
    assert chat_response.status_code == 200, chat_response.text
    payload = chat_response.json()
    assert payload["answer"]
    assert payload["intent"] in {"lookup", "summary", "facts", "comparison", "abstain"}
