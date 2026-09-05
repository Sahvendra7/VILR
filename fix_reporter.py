with open('simulator/reporter.py', 'r') as f:
    content = f.read()

content = content.replace('f.write("# Ground-Truth Security Evaluation Matrix\\n\\n")', 'f.write("# Ground-Truth Security Evaluation Matrix\\n\\n")')
# Wait, I can just rewrite reporter.py entirely to be safe and clean.
