import re

with open("scripts/cli.py", "r") as f:
    content = f.read()

replacement = """                    print("==================================================")
                    print("VILR SECURITY DECISION")
                    print("==================================================")
                    print(f"DECISION:\n{r.get('final_decision')}\n")
                    
                    if r.get("risk"):
                        risk = r["risk"]
                        print(f"RISK:\n{risk.get('level', 'LOW')} — {risk.get('score', 0)}")
                        factors = risk.get('factors', [])
                        if factors:
                            print("\nFACTORS:")
                            for factor in factors:
                                print(f"✗ {factor.get('signal')} +{factor.get('weight')}")
                        print("")
                        
                    print("AUTHORITY:\nOPA\n")
                    
                    if r.get("explanation") and "policy_version" in r.get("explanation"):
                        print(f"POLICY:\n{r.get('explanation').get('policy_name', 'payment_authorization')} {r.get('explanation').get('policy_version')}\n")
                        print(f"EXPLANATION:\n{r.get('explanation').get('message', 'Authorization denied by policy.')}\n")
                        
                    print(f"EXECUTION:\n{r.get('execution_status', 'NOT_REACHED')}\\n")
"""

content = re.sub(r'                    print\("=================================================="\)\n                    print\("VILR SECURITY DECISION"\)\n                    print\("=================================================="\)\n                    print\(f"Decision:\\n\{r\.get\(\'final_decision\'\)\}\\n"\)\n.*?print\("\\nSemantic:\\n✓ advisory evidence"\)', replacement, content, flags=re.DOTALL)

with open("scripts/cli.py", "w") as f:
    f.write(content)
