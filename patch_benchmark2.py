import re

with open("scripts/cli.py", "r") as f:
    content = f.read()

# Fix broken print statements
content = content.replace('print("\\n================', 'print("\\n================')
# That might not fix it if it's literally a newline in the file

# Let's just fix it purely by line replacements
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'print("' in line and line.endswith('\\'):
        # Fix trailing slash or literal newline
        pass
