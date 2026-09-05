with open("scripts/cli.py", "r") as f:
    content = f.read()

replacement = """    def print_metric(name, display_name):
        arr = metrics.get(name, [])
        if not arr:
            print(f"\\n{display_name}\\nP50: NOT MEASURED\\nP95: NOT MEASURED\\nP99: NOT MEASURED")
            return
            
        arr.sort()
        import math
        def pct(p):
            idx = int(math.ceil(p / 100.0 * len(arr))) - 1
            return arr[max(0, idx)]
            
        p50 = pct(50)
        p95 = pct(95)
        p99 = pct(99)
        print(f"\\n{display_name}\\nP50: {p50:.2f} ms\\nP95: {p95:.2f} ms\\nP99: {p99:.2f} ms")"""

import re
content = re.sub(r'    def print_metric.*?ms"\)', replacement, content, flags=re.DOTALL)
content = content.replace("import numpy as np", "")

with open("scripts/cli.py", "w") as f:
    f.write(content)
