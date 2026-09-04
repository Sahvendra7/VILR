import re

with open("scripts/cli.py", "r") as f:
    text = f.read()

match = re.search(r'async def run_demo\(args\):.*?(?=async def run_hero|def main\(\))', text, flags=re.DOTALL)
if not match:
    print("Could not find run_demo")
    exit(1)

old_demo = match.group(0)

with open("demo_template.txt", "r") as f:
    new_demo = f.read()

text = text.replace(old_demo, new_demo + "\n")

with open("scripts/cli.py", "w") as f:
    f.write(text)

