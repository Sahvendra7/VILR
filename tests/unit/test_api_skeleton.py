import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    # Even if services are down, the endpoint returns 200 with status objects
    assert response.status_code == 200
    assert "status" in response.json()

def test_intents_not_implemented():
    response = client.post("/v1/intents", json={"intent": {}})
    assert response.status_code == 422 # Schema validation fails first

    # Provide schema valid body
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
    response2 = client.post("/v1/intents", json=valid_body)
    assert response2.status_code == 501

def test_authorize_not_implemented():
    response = client.post("/v1/authorize", json={
        "transaction_id": "t1",
        "open_checkout_token": "token1",
        "closed_checkout_token": "token2",
        "user_intent": {
            "user_id": "u1",
            "raw_prompt": "x",
            "semantic_intent": "y",
            "hard_constraints": {"max_budget": "10", "currency": "USD"},
            "soft_preferences": {}
        },
        "cart": {
            "items": [],
            "total_amount": "0",
            "currency": "USD",
            "merchant_id": "m1"
        }
    })
    assert response.status_code == 501

def test_execute_not_implemented():
    response = client.post("/v1/execute", json={
        "transaction_id": "t1",
        "open_payment_token": "t1",
        "closed_payment_token": "t2"
    })
    assert response.status_code == 501
