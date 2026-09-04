with open("scripts/cli.py", "r") as f:
    lines = f.readlines()

start_idx = 0
end_idx = 0
for i, line in enumerate(lines):
    if line.startswith("async def run_demo(args):"):
        start_idx = i
    elif line.startswith("async def run_hero(args):"):
        end_idx = i
        break

with open("demo_template.txt", "r") as f:
    demo_lines = f.readlines()

new_lines = lines[:start_idx] + demo_lines + ["\n"] + lines[end_idx:]

with open("scripts/cli.py", "w") as f:
    f.writelines(new_lines)
