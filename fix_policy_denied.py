with open("app/domain/gateway.py", "r") as f:
    content = f.read()

content = content.replace("PolicyViolation", "PolicyDenied")

with open("app/domain/gateway.py", "w") as f:
    f.write(content)
