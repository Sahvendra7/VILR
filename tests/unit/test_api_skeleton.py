import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_health():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert "status" in response.json()

def test_intents_implemented():
    with TestClient(app) as client:
        valid_body = {
            "intent": {
                "user_id": "u1",
                "raw_prompt": "buy this",
                "semantic_intent": "buy",
                "hard_constraints": {
                    "max_budget": "100.00",
                    "currency": "USD"
                },
                "soft_preferences": {}
            }
        }
        response = client.post("/v1/intents", json=valid_body)
        assert response.status_code == 200

# Other routes like authorize/execute will throw 500 or validation errors without a properly mocked state/redis,
# but our integration tests handle their behavior. We just need to make sure the app loads.
