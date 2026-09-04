import re
with open("scripts/cli.py", "r") as f:
    text = f.read()

replacement = """async def run_demo(args):
    from app.semantic.provider import get_provider
    from app.semantic.verifier import AISemanticVerifier
    from app.core.config import settings
    
    generator = ScenarioGenerator()
    async with app.router.lifespan_context(app), AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        
        if getattr(args, "llm", "mock") == "gemini":
            print("==================================================")
            print("INITIALIZING GEMINI API PROVIDER...")
            print("==================================================")
            provider = get_provider("gemini", api_key=settings.gemini_api_key, model=settings.gemini_model)
            app.state.gateway.semantic = AISemanticVerifier(provider)
        """

text = text.replace("""async def run_demo(args):
    generator = ScenarioGenerator()
    async with app.router.lifespan_context(app), AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:""", replacement)

with open("scripts/cli.py", "w") as f:
    f.write(text)
