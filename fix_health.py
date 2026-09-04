import re
with open("app/main.py", "r") as f:
    content = f.read()

content = content.replace("redis_status = f\"error: {str(e)}\"", "redis_status = \"unavailable\"")
content = content.replace("opa_status = f\"error: {str(e)}\"", "opa_status = \"unavailable\"")

with open("app/main.py", "w") as f:
    f.write(content)
