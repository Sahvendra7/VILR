import re
with open("app/config/settings.py", "r") as f:
    text = f.read()

text = text.replace('gemini_model: str = "gemini-2.5-flash"', 'gemini_model: str = "gemini-3.6-flash"')

with open("app/config/settings.py", "w") as f:
    f.write(text)

with open("app/semantic/provider.py", "r") as f:
    text = f.read()

text = text.replace('gemini-2.5-flash', 'gemini-3.6-flash')

with open("app/semantic/provider.py", "w") as f:
    f.write(text)

with open("tests/integration/test_gemini_provider.py", "r") as f:
    text = f.read()

text = text.replace('gemini-2.5-flash', 'gemini-3.6-flash')

with open("tests/integration/test_gemini_provider.py", "w") as f:
    f.write(text)
