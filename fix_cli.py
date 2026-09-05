import re

with open("scripts/cli.py", "r") as f:
    content = f.read()

# find def print_receipt_demo up to "print("Receipt not found")"
start_idx = content.find("async def print_receipt_demo(tx_id, title):")
end_idx = content.find("def parse_args():")

new_func = """async def print_receipt_demo(tx_id, title):
                print(f"\\n==================================================")
                print(f"{title}")
                print(f"==================================================")
                rec_resp = await client.get(f"/v1/receipt/{tx_id}")
                if rec_resp.status_code == 200:
                    r = rec_resp.json()
                    print("==================================================")
                    print("VILR SECURITY DECISION")
                    print("==================================================")
                    print(f"DECISION:\\n{r.get('final_decision')}\\n")
                    
                    if r.get("risk"):
                        risk = r["risk"]
                        print(f"RISK:\\n{risk.get('level', 'LOW')} — {risk.get('score', 0)}")
                        factors = risk.get('factors', [])
                        if factors:
                            print("\\nFACTORS:")
                            for factor in factors:
                                print(f"✗ {factor.get('signal')} +{factor.get('weight')}")
                        print("")
                        
                    print("AUTHORITY:\\nOPA\\n")
                    
                    if r.get("explanation") and "policy_version" in r.get("explanation"):
                        print(f"POLICY:\\n{r.get('explanation').get('policy_name', 'payment_authorization')} {r.get('explanation').get('policy_version')}\\n")
                        print(f"EXPLANATION:\\n{r.get('explanation').get('message', 'Authorization denied by policy.')}\\n")
                        
                    print(f"EXECUTION:\\n{r.get('execution_status', 'NOT_REACHED')}\\n")
                else:
                    print("Receipt not found")

        # Now for demo run blocks:
"""

# I need a surgical regex or string index replacement.
def fix_file():
    with open("scripts/cli.py", "r") as f:
        lines = f.readlines()
    
    out = []
    in_receipt = False
    for line in lines:
        if "async def print_receipt_demo" in line:
            in_receipt = True
            out.append("            async def print_receipt_demo(tx_id, title):\n")
            out.append("                print(f\"\\n==================================================\")\n")
            out.append("                print(f\"{title}\")\n")
            out.append("                print(f\"==================================================\")\n")
            out.append("                rec_resp = await client.get(f\"/v1/receipt/{tx_id}\")\n")
            out.append("                if rec_resp.status_code == 200:\n")
            out.append("                    r = rec_resp.json()\n")
            out.append("                    print(\"==================================================\")\n")
            out.append("                    print(\"VILR SECURITY DECISION\")\n")
            out.append("                    print(\"==================================================\")\n")
            out.append("                    print(f\"DECISION:\\n{r.get('final_decision')}\\n\")\n")
            out.append("                    if r.get(\"risk\"):\n")
            out.append("                        risk = r[\"risk\"]\n")
            out.append("                        print(f\"RISK:\\n{risk.get('level', 'LOW')} — {risk.get('score', 0)}\")\n")
            out.append("                        factors = risk.get('factors', [])\n")
            out.append("                        if factors:\n")
            out.append("                            print(\"\\nFACTORS:\")\n")
            out.append("                            for factor in factors:\n")
            out.append("                                print(f\"✗ {factor.get('signal')} +{factor.get('weight')}\")\n")
            out.append("                        print(\"\")\n")
            out.append("                    print(\"AUTHORITY:\\nOPA\\n\")\n")
            out.append("                    if r.get(\"explanation\") and \"policy_version\" in r.get(\"explanation\"):\n")
            out.append("                        print(f\"POLICY:\\n{r.get('explanation').get('policy_name', 'payment_authorization')} {r.get('explanation').get('policy_version')}\\n\")\n")
            out.append("                        print(f\"EXPLANATION:\\n{r.get('explanation').get('message', 'Authorization denied by policy.')}\\n\")\n")
            out.append("                    print(f\"EXECUTION:\\n{r.get('execution_status', 'NOT_REACHED')}\\n\")\n")
            out.append("                else:\n")
            out.append("                    print(\"Receipt not found\")\n")
            continue
            
        if in_receipt:
            if "print(\"\\n==================================================\")" in line and "SCENARIO 1" in "".join(lines[lines.index(line):lines.index(line)+3]):
                in_receipt = False
                out.append(line)
            elif "print(\"\\n==================================================\")" in line and "SCENARIO" in line:
                 pass
            elif line.strip().startswith("print(\"\\n==================================================\")") and "SCENARIO 1" in lines[lines.index(line)+1]:
                in_receipt = False
                out.append(line)
            elif "SCENARIO 1" in line:
                in_receipt = False
                out.append('            print("\\n==================================================")\n')
                out.append(line)
            continue
            
        out.append(line)
        
    with open("scripts/cli.py", "w") as f:
        f.writelines(out)

fix_file()
