import re

with open("scripts/cli.py", "r") as f:
    content = f.read()

new_func = """            async def print_receipt_demo(tx_id, title):
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
"""
content = re.sub(r'            async def print_receipt_demo\(tx_id, title\):.*?else:\n                    print\("Receipt not found"\)', new_func, content, flags=re.DOTALL)

with open("scripts/cli.py", "w") as f:
    f.write(content)
