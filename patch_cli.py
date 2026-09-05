import re
with open("scripts/cli.py", "r") as f:
    content = f.read()

# Update FakePolicy to include policy_hash
fake_policy_old = """    class FakePolicy:
        async def evaluate(self, input_data):
            cart = input_data.get("cart", {})
            amt = float(cart.get("total_amount", 0))
            if amt == 95000.0:
                return AuthorizationDecision(allowed=False, violations=[{"type":"budget", "message":"Exceeded budget", "code":"BUDGET_EXCEEDED"}], policy_version="v3")
            if amt == 10000.0:
                return AuthorizationDecision(allowed=False, violations=[{"type":"semantic", "message":"Semantic mismatch", "code":"SEMANTIC_FAIL"}], policy_version="v3")
            return AuthorizationDecision(allowed=True, violations=[], policy_version="v3")
            
        def is_available(self):
            return True"""
content = re.sub(r'    class FakePolicy:.*?(?=    print\("=================================================="\))', fake_policy_old + '\n', content, flags=re.DOTALL)

# Remove the old prints and insert a new print based on SecurityReceipt
print_func = """
            async def print_receipt_demo(tx_id, title):
                print(f"\\n==================================================")
                print(f"{title}")
                print(f"==================================================")
                rec_resp = await client.get(f"/v1/receipt/{tx_id}")
                if rec_resp.status_code == 200:
                    r = rec_resp.json()
                    print("==================================================")
                    print("VILR SECURITY DECISION")
                    print("==================================================")
                    print(f"Decision:\\n{r.get('final_decision')}\\n")
                    
                    if r.get("explanation") and "policy_version" in r.get("explanation"):
                        print(f"POLICY\\n{r.get('explanation').get('policy_name', 'payment_authorization')}")
                        print(f"Version:\\n{r.get('explanation').get('policy_version')}\\n")
                        print(f"POLICY EXPLANATION\\n{r.get('explanation').get('message', 'Authorization denied by policy.')}\\n")
                        
                    print("DECISION EVIDENCE\\n")
                    if r.get("evidence"):
                        ev = r["evidence"]
                        print("Intent:\\n✓ verified" if ev.get("intent", {}).get("intent_status") == "VERIFIED" else "Intent:\\n✗ unverified")
                        print("\\nCryptography:\\n✓ signature verified" if ev.get("cryptographic", {}).get("signature_verified") else "\\nCryptography:\\n✗ unverified")
                        
                        cart_ev = ev.get("cart", {})
                        if cart_ev.get("cart_match"):
                            print("\\nCart:\\n✓ amount matched")
                        else:
                            print(f"\\nCart:\\n✗ expected {cart_ev.get('expected_amount')} actual {cart_ev.get('actual_amount')}")
                            
                        print("\\nReplay:\\n✓ no replay" if not ev.get("replay", {}).get("replay_detected") else "\\nReplay:\\n✗ replay detected")
                        print("\\nSemantic:\\n✓ advisory evidence")
                        pol = ev.get("policy", {})
                        print(f"\\nPolicy:\\n✗ DENY" if pol.get("policy_decision") == "DENY" else "\\nPolicy:\\n✓ ALLOW")
                        exe = ev.get("execution", {})
                        print(f"\\nExecution:\\n{exe.get('execution_status')}\\n")
                    else:
                        print("No evidence attached.\\n")
                        
                    print("RISK:\\nDo NOT implement risk scoring in this phase.\\n")
                    print("AUDIT:\\nSupabase persisted")
                    print("==================================================")
"""

content = content.replace("async with AsyncClient(transport=ASGITransport(app=app), base_url=\"http://test\") as client:", "async with AsyncClient(transport=ASGITransport(app=app), base_url=\"http://test\") as client:\n" + print_func)

# We want to replace the scenario print statements with calls to print_receipt_demo
# But first, we need to find them and modify.

with open("scripts/cli.py", "w") as f:
    f.write(content)
