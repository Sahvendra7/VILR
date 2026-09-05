with open("app/domain/gateway.py", "r") as f:
    content = f.read()

content = content.replace(
    "\"investigation\": kwargs.get(\"investigation\")",
    "\"investigation\": kwargs.get(\"investigation\"),\n            \"evidence\": kwargs.get(\"evidence\"),\n            \"explanation\": kwargs.get(\"explanation\")"
)
with open("app/domain/gateway.py", "w") as f:
    f.write(content)
