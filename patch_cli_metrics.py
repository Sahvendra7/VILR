import re

with open('scripts/cli.py', 'r') as f:
    content = f.read()

metrics_func = """
async def run_metrics(args):
    import json
    import os
    print("==================================================")
    print("VILR METRICS DASHBOARD")
    print("==================================================")
    
    # Load from actual evaluation data
    benchmark_path = "results/security-benchmark.json"
    if not os.path.exists(benchmark_path):
        print("No evaluation data found. Run 'security' first.")
        return
        
    with open(benchmark_path, "r") as f:
        data = json.load(f)
        
    vilr = data.get("VILR", [])
    
    attacks = [r for r in vilr if r["category"] not in ["VALID", "Robustness", "Regression"]]
    valid_tx = [r for r in vilr if r["category"] == "VALID"]
    replay_tx = [r for r in vilr if r["category"] == "Replay"]
    concurrency_tx = [r for r in vilr if r["category"] == "Concurrency"]
    
    attacks_incorrectly_authorized = len([r for r in attacks if r["actual_decision"] == "ALLOW"])
    relevant_attack_attempts = len(attacks)
    far = (attacks_incorrectly_authorized / relevant_attack_attempts * 100) if relevant_attack_attempts else 0
    
    blocked_attack_attempts = len([r for r in attacks if r["actual_decision"] == "DENY"])
    blocked_causing_side_effects = len([r for r in attacks if r["actual_decision"] == "DENY" and r["actual_side_effect"] == "PAYMENT_EXECUTED"])
    
    blocked_replay = len([r for r in replay_tx if r["actual_decision"] == "DENY"])
    replay_attempts = len(replay_tx)
    replay_rate = (blocked_replay / replay_attempts * 100) if replay_attempts else 0
    
    duplicate_payments = len([r for r in concurrency_tx if r["actual_side_effect"] == "PAYMENT_EXECUTED"])
    duplicate_attempts = len(concurrency_tx)
    duplicate_rate = (duplicate_payments / duplicate_attempts * 100) if duplicate_attempts else 0
    
    cart_tamper = [r for r in vilr if r["attack_id"] == "T-03"]
    cart_tamper_detected = len([r for r in cart_tamper if r["actual_decision"] == "DENY"])
    cart_tamper_rate = (cart_tamper_detected / len(cart_tamper) * 100) if cart_tamper else 0
    
    policy_denials = len([r for r in vilr if r["category"] == "Policy" and r["actual_decision"] == "DENY"])

    print("\\nSECURITY:")
    print(f"- False Authorization Rate: {far:.1f}%")
    print(f"- Replay Prevention Rate: {replay_rate:.1f}%")
    print(f"- Duplicate Execution Rate: {duplicate_rate:.1f}%")
    print(f"- Provider Side-Effect Count: {blocked_causing_side_effects}")
    print(f"- Cart Tampering Detection: {cart_tamper_rate:.1f}%")
    print(f"- Policy Denials: {policy_denials}")

    print("\\nAI:")
    print("- Gemini semantic result: MEASURED VIA EVALUATION")
    print("- Gemini latency: NOT MEASURED (Mock in CLI)")
    print("- Exception Investigation result: NOT MEASURED")
    print("- Exception Investigation latency: NOT MEASURED")

    print("\\nPAYMENTS:")
    authorized = len([r for r in vilr if r["actual_decision"] == "ALLOW"])
    denied = len([r for r in vilr if r["actual_decision"] == "DENY"])
    failed = len([r for r in vilr if r["actual_decision"] == "ERROR"])
    unknown = len([r for r in vilr if r["actual_decision"] == "UNKNOWN"])
    print(f"- Authorized: {authorized}")
    print(f"- Denied: {denied}")
    print(f"- Failed: {failed}")
    print(f"- Unknown: {unknown}")

    print("\\nAUDIT:")
    print(f"- Records persisted: {len(vilr)}")
    print("- Chain valid: True (simulated in CLI)")
    print(f"- Tampering detected: {len([r for r in vilr if r['actual_decision'] == 'DETECTED'])}")

    print("\\nRECOVERY:")
    print("- PAYMENT_UNKNOWN cases: IMPLEMENTED")
    print("- reconciliation-required cases: IMPLEMENTED")
    print("- recovery recommendations: EXTENSION POINT")
    print("==================================================")
"""

content = content.replace("async def run_hero(args):", metrics_func + "\nasync def run_hero(args):")

content = content.replace(
    'p_sec_demo = subparsers.add_parser("security-demo")',
    'p_sec_demo = subparsers.add_parser("security-demo")\n    p_metrics = subparsers.add_parser("metrics")'
)

content = content.replace(
    'elif args.command == "security-demo":\n        asyncio.run(run_security_demo(args))',
    'elif args.command == "security-demo":\n        asyncio.run(run_security_demo(args))\n    elif args.command == "metrics":\n        asyncio.run(run_metrics(args))'
)

with open('scripts/cli.py', 'w') as f:
    f.write(content)
