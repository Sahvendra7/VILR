import json
from typing import List, Dict
from simulator.models import AttackResult, AttackOutcome

class Reporter:
    def __init__(self, results: Dict[str, List[AttackResult]]):
        self.results = results

    def generate_json(self, path: str):
        out = {}
        for baseline, res_list in self.results.items():
            out[baseline] = [r.__dict__ for r in res_list]
        with open(path, "w") as f:
            json.dump(out, f, indent=2)

    def generate_markdown(self, path: str):
        with open(path, "w") as f:
            f.write("# Security Benchmark Report\n\n")
            f.write("## 1. Executive Summary\n")
            f.write("This report benchmarks the VILR Gateway Orchestrator against adversarial attacks and compares it with three baselines.\n\n")

            f.write("## 2. Attack Results\n\n")
            f.write("| Attack ID | Name | Baseline A | Baseline B | Baseline C | VILR | Defense Layer |\n")
            f.write("|---|---|---|---|---|---|---|\n")

            if not self.results:
                return

            vilr_results = {r.attack_id: r for r in self.results["VILR"]}
            ba_results = {r.attack_id: r for r in self.results.get("Baseline_A", [])}
            bb_results = {r.attack_id: r for r in self.results.get("Baseline_B", [])}
            bc_results = {r.attack_id: r for r in self.results.get("Baseline_C", [])}

            counts = {
                "BLOCKED": 0,
                "DETECTED": 0,
                "NOT_BLOCKED": 0,
                "ERROR": 0,
                "INCONCLUSIVE": 0
            }

            for attack_id, vilr_res in vilr_results.items():
                counts[vilr_res.outcome.value] += 1
                
                ba = ba_results.get(attack_id)
                bb = bb_results.get(attack_id)
                bc = bc_results.get(attack_id)

                ba_str = ba.outcome.value if ba else "N/A"
                bb_str = bb.outcome.value if bb else "N/A"
                bc_str = bc.outcome.value if bc else "N/A"
                vilr_str = vilr_res.outcome.value

                f.write(f"| {attack_id} | {vilr_res.name} | {ba_str} | {bb_str} | {bc_str} | {vilr_str} | {vilr_res.defense_layer} |\n")

            total_attacks = sum(counts.values())
            security_success = counts["BLOCKED"] + counts["DETECTED"]
            unresolved = counts["ERROR"] + counts["INCONCLUSIVE"]
            security_failure = counts["NOT_BLOCKED"]
            
            pass_rate = (security_success / total_attacks * 100) if total_attacks > 0 else 0.0

            f.write("\n## 3. Security Metrics\n\n")
            f.write(f"- Total Attacks: {total_attacks}\n")
            f.write(f"- BLOCKED: {counts['BLOCKED']}\n")
            f.write(f"- DETECTED: {counts['DETECTED']}\n")
            f.write(f"- NOT_BLOCKED: {counts['NOT_BLOCKED']}\n")
            f.write(f"- ERROR: {counts['ERROR']}\n")
            f.write(f"- INCONCLUSIVE: {counts['INCONCLUSIVE']}\n")
            f.write(f"- Security Success Rate: {pass_rate:.1f}% (Calculated as [BLOCKED + DETECTED] / Total)\n")

