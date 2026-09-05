with open("scripts/cli.py", "r") as f:
    content = f.read()

# Replace all literal newlines inside prints
import re

content = re.sub(r'print\(f"\n(.*?)\nP50', r'print(f"\\n\1\\nP50', content)
content = content.replace('P50: NOT MEASURED\nP95: NOT MEASURED\nP99: NOT MEASURED")', 'P50: NOT MEASURED\\nP95: NOT MEASURED\\nP99: NOT MEASURED")')
content = content.replace('P50: {p50:.2f} ms\nP95: {p95:.2f} ms\nP99: {p99:.2f} ms")', 'P50: {p50:.2f} ms\\nP95: {p95:.2f} ms\\nP99: {p99:.2f} ms")')

with open("scripts/cli.py", "w") as f:
    f.write(content)

