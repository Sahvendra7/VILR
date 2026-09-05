import re
with open("scripts/cli.py", "r") as f:
    content = f.read()

# I will replace the weird leftover lines with nothing.
leftover = """                        pol = ev.get("policy", {})
                        print(f"\\nPolicy:\\n✗ DENY" if pol.get("policy_decision") == "DENY" else "\\nPolicy:\\n✓ ALLOW")
                        exe = ev.get("execution", {})
                        print(f"\\nExecution:\\n{exe.get('execution_status')}\\n")
                    else:
                        print("No evidence attached.\\n")
                        
                    print("RISK:\\nDo NOT implement risk scoring in this phase.\\n")
                    print("AUDIT:\\nSupabase persisted")"""

content = content.replace(leftover, "")
with open("scripts/cli.py", "w") as f:
    f.write(content)
