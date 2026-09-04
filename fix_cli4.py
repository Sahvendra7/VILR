with open("scripts/cli.py", "r") as f:
    text = f.read()

import re

# We need to add async with app.router.lifespan_context(app) before we touch app.state
lifespan_wrapper = r"""
    async with app.router.lifespan_context(app):
        if args.llm == "mock":
            from app.semantic.provider import MockLLMProvider
            from app.semantic.verifier import AISemanticVerifier
            mock_provider_llm = MockLLMProvider()
            app.state.gateway.semantic = AISemanticVerifier(mock_provider_llm)
        else:
            from app.semantic.provider import GeminiLLMProvider
            from app.semantic.verifier import AISemanticVerifier
            gemini = GeminiLLMProvider()
            app.state.gateway.semantic = AISemanticVerifier(gemini)

        app.state.gateway.idempotency = FakeIdempotencyStore()
        app.state.gateway.policy.is_available = lambda: True
        generator = ScenarioGenerator()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
"""

text = re.sub(r'    if args.llm == "mock":.*?(?=            print\("\\n==================================================")', lifespan_wrapper, text, flags=re.DOTALL)

with open("scripts/cli.py", "w") as f:
    f.write(text)
