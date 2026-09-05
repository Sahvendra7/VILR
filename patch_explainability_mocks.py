with open("app/policy/explainability.py", "r") as f:
    content = f.read()

content = content.replace("message=violation.get(\"message\", \"Authorization denied by policy.\")", "message=str(violation.get(\"message\", \"Authorization denied by policy.\"))")

with open("app/policy/explainability.py", "w") as f:
    f.write(content)
