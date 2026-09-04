with open("app/main.py", "r") as f:
    text = f.read()

text = text.replace(
    "semantic_provider = get_provider(settings.llm_provider)",
    "semantic_provider = get_provider(settings.llm_provider, api_key=settings.gemini_api_key, model=settings.gemini_model)"
)

with open("app/main.py", "w") as f:
    f.write(text)
