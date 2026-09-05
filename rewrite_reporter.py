import re

with open('simulator/reporter.py', 'r') as f:
    content = f.read()

# Update the markdown output to include the new evaluation results

new_report_code = """
    def generate_markdown(self, path: str):
        with open(path, "w") as f:
            f.write("# Ground-Truth Security Evaluation Matrix\\n\\n")
            
            f.write("## 1. Evaluation Results\\n\\n")
            f.write("| Case ID | Name | Category | Expected Decision | Actual Decision | Expected Side-Effect | Actual Side-Effect | Status | Error |\\n")
            f.write("|---|---|---|---|---|---|---|---|---|\\n")

            counts = {
                "PASS": 0,
                "FAIL": 0
            }
            
            total_cases = len(self.vilr)
            valid_cases = len([r for r in self.vilr if r.category == "VALID"])
            security_attacks = len([r for r in self.vilr if r.category not in ["VALID", "Regression", "Robustness"]])
            regression_cases = len([r for r in self.vilr if r.category == "Regression"])
            robustness_cases = len([r for r in self.vilr if r.category == "Robustness"])
            
            blocked = len([r for r in self.vilr if r.actual_decision == "DENY" and r.category != "VALID"])
            detected = len([r for r in self.vilr if r.actual_decision == "DETECTED"])
            not_blocked = len([r for r in self.vilr if r.actual_decision == "ALLOW" and r.category != "VALID"])
            errors = len([r for r in self.vilr if r.actual_decision == "ERROR"])
            inconclusive = len([r for r in self.vilr if r.actual_decision == "UNKNOWN"])
            
            payment_calls = 0
            payment_creations = 0

            for r in self.vilr:
                counts[r.status] += 1
                payment_calls += r.payment_call_count
                payment_creations += r.payment_creation_count
                
                f.write(f"| {r.case_id} | {r.name} | {r.category} | {r.expected_decision.value} | {r.actual_decision.value} | {r.expected_side_effect.value} | {r.actual_side_effect.value} | {r.status} | {r.error} |\\n")

            f.write("\\n## 2. Security Metrics\\n\\n")
            
            attacks = [r for r in self.vilr if r.category != "VALID" and r.category != "Robustness"]
            valid_tx = [r for r in self.vilr if r.category == "VALID"]
            replay_tx = [r for r in self.vilr if r.category == "Replay"]
            concurrency_tx = [r for r in self.vilr if r.category == "Concurrency"]
            
            attacks_incorrectly_authorized = len([r for r in attacks if r.actual_decision == "ALLOW"])
            relevant_attack_attempts = len(attacks)
            far = (attacks_incorrectly_authorized / relevant_attack_attempts * 100) if relevant_attack_attempts else 0
            
            blocked_attack_attempts = len([r for r in attacks if r.actual_decision == "DENY"])
            blocked_causing_side_effects = len([r for r in attacks if r.actual_decision == "DENY" and r.actual_side_effect == "PAYMENT_EXECUTED"])
            
            blocked_replay = len([r for r in replay_tx if r.actual_decision == "DENY"])
            replay_attempts = len(replay_tx)
            
            duplicate_payments = len([r for r in concurrency_tx if r.actual_side_effect == "PAYMENT_EXECUTED"])
            duplicate_attempts = len(concurrency_tx)
            
            valid_denied = len([r for r in valid_tx if r.actual_decision == "DENY"])
            valid_total = len(valid_tx)
            
            unknown_failure_rate = len([r for r in self.vilr if r.actual_decision in ["UNKNOWN", "ERROR"]]) / len(self.vilr) * 100 if len(self.vilr) else 0

            f.write(f"- False Authorization Rate: {far:.1f}% ({attacks_incorrectly_authorized}/{relevant_attack_attempts})\\n")
            f.write(f"- Provider Side-Effect Rate: {blocked_causing_side_effects}/{blocked_attack_attempts}\\n")
            f.write(f"- Replay Prevention Rate: {blocked_replay}/{replay_attempts}\\n")
            f.write(f"- Duplicate Execution Rate: {duplicate_payments}/{duplicate_attempts}\\n")
            f.write(f"- False Denial Rate: {valid_denied}/{valid_total}\\n")
            f.write(f"- Unknown/Failure Rate: {unknown_failure_rate:.1f}%\\n")

            f.write("\\n## 3. Summary Statistics\\n\\n")
            f.write(f"Total cases: {total_cases}\\n")
            f.write(f"Valid: {valid_cases}\\n")
            f.write(f"Security attacks: {security_attacks}\\n")
            f.write(f"Regression: {regression_cases}\\n")
            f.write(f"Robustness: {robustness_cases}\\n")
            f.write(f"Blocked: {blocked}\\n")
            f.write(f"Detected: {detected}\\n")
            f.write(f"Not blocked: {not_blocked}\\n")
            f.write(f"Errors: {errors}\\n")
            f.write(f"Inconclusive: {inconclusive}\\n")
"""

content = re.sub(
    r'    def generate_markdown\(self, path: str\):.*?(?=    def generate_baseline_comparison)',
    new_report_code,
    content,
    flags=re.DOTALL
)

with open('simulator/reporter.py', 'w') as f:
    f.write(content)
