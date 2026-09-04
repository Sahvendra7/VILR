import re
with open("pyproject.toml", "r") as f:
    text = f.read()

text = text.replace('"anthropic>=0.40",', '"anthropic>=0.40",\n    "google-genai>=0.5.0",\n    "fakeredis>=2.0",')

with open("pyproject.toml", "w") as f:
    f.write(text)

with open("app/config/settings.py", "r") as f:
    text = f.read()

text = text.replace('anthropic_api_key: str = ""', 'anthropic_api_key: str = ""\n    gemini_api_key: str = ""\n    gemini_model: str = "gemini-2.5-flash"')
with open("app/config/settings.py", "w") as f:
    f.write(text)
