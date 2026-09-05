import json
with open('results/security-benchmark.json') as f:
    d = json.load(f)
for r in d.get("VILR", []):
    if r["case_id"] == "V-01":
        print("V-01:", r)
