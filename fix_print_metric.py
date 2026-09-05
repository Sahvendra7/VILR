import re

with open("scripts/cli.py", "r") as f:
    content = f.read()

# Replace from def print_metric to the end of that function
def_metric = r"""    def print_metric(name, display_name):
        arr = metrics.get(name, [])
        if not arr:
            print(f"\n{display_name}\nP50: NOT MEASURED\nP95: NOT MEASURED\nP99: NOT MEASURED")
            return
            
        arr.sort()
        import math
        def pct(p):
            idx = int(math.ceil(p / 100.0 * len(arr))) - 1
            return arr[max(0, idx)]
            
        p50 = pct(50)
        p95 = pct(95)
        p99 = pct(99)
        print(f"\n{display_name}\nP50: {p50:.2f} ms\nP95: {p95:.2f} ms\nP99: {p99:.2f} ms")"""

# Because of literal newlines, I will just find "def print_metric" and replace up to "print_metric("deterministic_authorization""
idx_start = content.find("    def print_metric(name, display_name):")
idx_end = content.find("    print_metric(\"deterministic_authorization\", \"Deterministic Authorization\")")

if idx_start != -1 and idx_end != -1:
    new_func = r"""    def print_metric(name, display_name):
        arr = metrics.get(name, [])
        if not arr:
            print("\n" + display_name + "\nP50: NOT MEASURED\nP95: NOT MEASURED\nP99: NOT MEASURED")
            return
            
        arr.sort()
        import math
        def pct(p):
            idx = int(math.ceil(p / 100.0 * len(arr))) - 1
            return arr[max(0, idx)]
            
        p50 = pct(50)
        p95 = pct(95)
        p99 = pct(99)
        print("\n" + display_name + f"\nP50: {p50:.2f} ms\nP95: {p95:.2f} ms\nP99: {p99:.2f} ms")

"""
    # Fix the newlines inside new_func to be literal escaped \n for the print statement!
    new_func = new_func.replace(r"\n", "\\n")
    
    content = content[:idx_start] + new_func + content[idx_end:]

with open("scripts/cli.py", "w") as f:
    f.write(content)
