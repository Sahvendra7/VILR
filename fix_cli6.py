with open("scripts/cli.py", "r") as f:
    text = f.read()

import re
match = re.search(r'async def run_demo\(args\):.*?(?=async def run_hero|def main\(\))', text, flags=re.DOTALL)
if match:
    old_demo = match.group(0)
    with open("demo_template.txt", "r") as f_template:
        new_demo = f_template.read()
    text = text.replace(old_demo, new_demo)
    with open("scripts/cli.py", "w") as f:
        f.write(text)
