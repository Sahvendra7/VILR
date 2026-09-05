with open("scripts/cli.py", "r") as f:
    content = f.read()

content = content.replace('print("\n==================================================")', 'print("\\n==================================================")')
content = content.replace('print(f"Environment:\nMac / Python / Simulated backend\nIterations: {iterations}")', 'print(f"Environment:\\nMac / Python / Simulated backend\\nIterations: {iterations}")')

content = content.replace('print(f"\n{display_name}\nP50: NOT MEASURED\nP95: NOT MEASURED\nP99: NOT MEASURED")', 'print(f"\\n{display_name}\\nP50: NOT MEASURED\\nP95: NOT MEASURED\\nP99: NOT MEASURED")')
content = content.replace('print(f"\n{display_name}\nP50: {p50:.2f} ms\nP95: {p95:.2f} ms\nP99: {p99:.2f} ms")', 'print(f"\\n{display_name}\\nP50: {p50:.2f} ms\\nP95: {p95:.2f} ms\\nP99: {p99:.2f} ms")')

with open("scripts/cli.py", "w") as f:
    f.write(content)
