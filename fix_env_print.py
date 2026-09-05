with open("scripts/cli.py", "r") as f:
    content = f.read()

idx_start = content.find('    print(f"Environment:\nMac / Python / Simulated backend\nIterations: {iterations}")')
if idx_start != -1:
    content = content[:idx_start] + '    print(f"Environment:\\nMac / Python / Simulated backend\\nIterations: {iterations}")' + content[idx_start+81:]

with open("scripts/cli.py", "w") as f:
    f.write(content)
