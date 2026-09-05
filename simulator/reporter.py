import json
from typing import List, Dict
from simulator.models import AttackResult, AttackOutcome

class Reporter:
    def __init__(self, results: Dict[str, List[AttackResult]]):
        self.results = results
        self.vilr = self.results.get("VILR", [])

    def generate_json(self, path: str):
        out = {}
        for baseline, res_list in self.results.items():
            out[baseline] = [r.__dict__ for r in res_list]
        with open(path, "w") as f:
            json.dump(out, f, indent=2)

    def generate_markdown(self, path: str):
        with open(path, "w") as f:
            f.write("# Ground-Truth Security Evaluation Matrix\n\n")

            f.write("## 1. Evaluation Results\n\n")
            f.write("| Case ID | Name | Category | Expected Decision | Actual Decision | Expected Side-Effect | Actual Side-Effect | Status | Error |\n")
            f.write("|---|---|---|---|---|---|---|---|---|\n")

            counts = {
                "PASS": 0,
                "FAIL": 0
            }

            total_cases = len(self.vilr)
            valid_cases = len([r for r in self.vilr if r.category == "VALID"])
            security_attacks = len([r for r in self.vilr if r.category not in ["VALID", "Regression", "Robustness"]])
            regression_cases = len([r for r in self.vilr if r.category == "Regression"])
            robustness_cases = len([r for r in self.vilr if r.category == "Robustness"])

            blocked = 0
            detected = 0
            not_blocked = 0
            errors = 0
            inconclusive = 0
            for r in self.vilr:
                if r.category == "VALID": continue
                if r.actual_decision.value == "DENY" and r.actual_side_effect.value == "NONE":
                    blocked += 1
                elif r.actual_decision.value == "DETECTED":
                    detected += 1
                elif r.actual_decision.value == "ALLOW" or r.actual_side_effect.value != "NONE":
                    not_blocked += 1
                elif r.actual_decision.value == "ERROR":
                    errors += 1
                else:
                    inconclusive += 1

            payment_calls = 0
            payment_creations = 0

            for r in self.vilr:
                counts[r.status] += 1
                payment_calls += r.payment_call_count
                payment_creations += r.payment_creation_count

                f.write(f"| {r.case_id} | {r.name} | {r.category} | {r.expected_decision.value} | {r.actual_decision.value} | {r.expected_side_effect.value} | {r.actual_side_effect.value} | {r.status} | {r.error} |\n")

            f.write("\n## 2. Security Metrics\n\n")

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

            f.write(f"- False Authorization Rate: {far:.1f}% ({attacks_incorrectly_authorized}/{relevant_attack_attempts})\n")
            f.write(f"- Provider Side-Effect Rate: {blocked_causing_side_effects}/{blocked_attack_attempts}\n")
            f.write(f"- Replay Prevention Rate: {blocked_replay}/{replay_attempts}\n")
            f.write(f"- Duplicate Execution Rate: {duplicate_payments}/{duplicate_attempts}\n")
            f.write(f"- False Denial Rate: {valid_denied}/{valid_total}\n")
            f.write(f"- Unknown/Failure Rate: {unknown_failure_rate:.1f}%\n")

            f.write("\n## 3. Summary Statistics\n\n")
            f.write(f"Total cases: {total_cases}\n")
            f.write(f"Valid: {valid_cases}\n")
            f.write(f"Security attacks: {security_attacks}\n")
            f.write(f"Regression: {regression_cases}\n")
            f.write(f"Robustness: {robustness_cases}\n")
            f.write(f"Blocked: {blocked}\n")
            f.write(f"Detected: {detected}\n")
            f.write(f"Not blocked: {not_blocked}\n")
            f.write(f"Errors: {errors}\n")
            f.write(f"Inconclusive: {inconclusive}\n")

    def generate_baseline_comparison(self, path: str):
        with open(path, "w") as f:
            f.write("# Baseline Comparison\n\n")
            f.write("| Attack | Category | Baseline A | Baseline B | Baseline C | VILR | Security Property Added |\n")
            f.write("|---|---|---|---|---|---|---|\n")

            ba_results = {r.attack_id: r for r in self.results.get("Baseline_A", [])}
            bb_results = {r.attack_id: r for r in self.results.get("Baseline_B", [])}
            bc_results = {r.attack_id: r for r in self.results.get("Baseline_C", [])}

            for vilr_res in self.vilr:
                attack_id = vilr_res.attack_id
                ba = ba_results.get(attack_id)
                bb = bb_results.get(attack_id)
                bc = bc_results.get(attack_id)

                ba_str = ba.actual_decision.value if ba else "N/A"
                bb_str = bb.actual_decision.value if bb else "N/A"
                bc_str = bc.actual_decision.value if bc else "N/A"
                vilr_str = vilr_res.actual_decision.value

                f.write(f"| {attack_id} | {vilr_res.category} | {ba_str} | {bb_str} | {bc_str} | {vilr_str} | {vilr_res.defense_layer} |\n")
