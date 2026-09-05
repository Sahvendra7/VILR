out = []
with open("scripts/cli.py", "r") as f:
    lines = f.readlines()

skip = False
for i, line in enumerate(lines):
    if line.strip() == 'print(f"':
        out.append('            print(f"\\\\n{display_name}\\\\nP50: NOT MEASURED\\\\nP95: NOT MEASURED\\\\nP99: NOT MEASURED")\n')
        # Skip next 4 lines
        for j in range(4):
            lines[i+j+1] = ""
    elif 'P50: {p50:.2f} ms' in line:
        pass
    else:
        out.append(line)

with open("scripts/cli.py", "w") as f:
    f.writelines(out)
