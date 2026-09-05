import re
with open("scripts/cli.py", "r") as f:
    content = f.read()

content = content.replace('    print_metric("evidence_construction", "Decision Evidence")', '    print_metric("evidence_construction", "Decision Evidence")\n    print_metric("risk_latency", "Risk")')
content = content.replace('"evidence_construction": [],', '"evidence_construction": [],\n        "risk_latency": [],')

with open("scripts/cli.py", "w") as f:
    f.write(content)
