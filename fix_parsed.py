import re
with open("app/semantic/provider.py", "r") as f:
    text = f.read()

text = text.replace("return response.parsed.model_dump()", "return response.parsed if isinstance(response.parsed, dict) else response.parsed.model_dump()")

with open("app/semantic/provider.py", "w") as f:
    f.write(text)
