import re
with open("tests/integration/test_gemini_provider.py", "r") as f:
    text = f.read()

text = text.replace("from app.core.config import settings", "from app.config.settings import settings")

with open("tests/integration/test_gemini_provider.py", "w") as f:
    f.write(text)
