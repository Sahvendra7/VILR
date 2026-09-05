with open("app/domain/gateway.py", "r") as f:
    content = f.read()

content = content.replace("datetime.now(UTC)", "datetime.now()")

with open("app/domain/gateway.py", "w") as f:
    f.write(content)
