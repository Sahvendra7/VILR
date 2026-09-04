import re
with open("app/semantic/provider.py", "r") as f:
    text = f.read()

text = text.replace("timeout=10.0", "timeout=30.0")

with open("app/semantic/provider.py", "w") as f:
    f.write(text)
