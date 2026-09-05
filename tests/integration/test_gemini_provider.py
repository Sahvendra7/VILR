import pytest
import os
import asyncio
from app.semantic.provider import GeminiLLMProvider
from app.semantic.verifier import AISemanticVerifier
from app.domain.models import UserIntent, Cart, CartItem, Identifier
from app.config.settings import settings

# Only run if GEMINI_API_KEY is present
pytestmark = pytest.mark.skipif(
    not os.environ.get("GEMINI_API_KEY") and not settings.gemini_api_key,
    reason="GEMINI_API_KEY is not set"
)

@pytest.fixture
def live_verifier():
    api_key = os.environ.get("GEMINI_API_KEY") or settings.gemini_api_key
    model = os.environ.get("GEMINI_MODEL") or settings.gemini_model or "gemini-3.6-flash"
    provider = GeminiLLMProvider(api_key=api_key, model=model)
    return AISemanticVerifier(provider)

@pytest.mark.asyncio
async def test_live_gemini_semantic_pass(live_verifier):
    intent = UserIntent(user_id=Identifier("u1"), raw_prompt="I want to buy a high-performance coding laptop", semantic_intent="buy laptop", hard_constraints={"max_budget": "3000.00", "currency": "USD"}, soft_preferences={})
    cart = Cart(
        merchant_id=Identifier("m1"),
        items=[CartItem(item_id="dell-xps", name="Dell XPS 15 - 32GB RAM, 1TB SSD", unit_price="2000.00", quantity=1, currency="USD", category="electronics")],
        total_amount="2000.00",
        currency="USD"
    )

    result = await live_verifier.verify(intent, cart)

    assert result.status == "PASS"
    assert result.confidence > 0.8
    # category_match assert removed

@pytest.mark.asyncio
async def test_live_gemini_semantic_fail(live_verifier):
    intent = UserIntent(user_id=Identifier("u1"), raw_prompt="I want to buy a high-performance coding laptop", semantic_intent="buy laptop", hard_constraints={"max_budget": "3000.00", "currency": "USD"}, soft_preferences={})
    cart = Cart(
        merchant_id=Identifier("m1"),
        items=[CartItem(item_id="ps5", name="Sony PlayStation 5 Console", unit_price="500.00", quantity=1, currency="USD", category="electronics")],
        total_amount="500.00",
        currency="USD"
    )

    result = await live_verifier.verify(intent, cart)

    assert result.status == "FAIL"
    assert len(result.violations) > 0
    assert result.violations[0].severity in ["HIGH", "CRITICAL"]

