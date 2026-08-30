import argparse
import asyncio
from simulator.runner import AttackRunner
from simulator.attacks import ATTACKS
from simulator.reporter import Reporter

async def main():
    parser = argparse.ArgumentParser(description="VILR Security CLI")
    parser.add_argument("command", choices=["security", "attack", "benchmark"])
    parser.add_argument("--attack", type=str, help="Specific attack ID to run")
    parser.add_argument("--category", type=str, help="Specific category to run")
    parser.add_argument("--baseline", action="store_true", help="Run against baselines")
    parser.add_argument("--json", type=str, help="Output JSON path")
    
    args = parser.parse_args()
    
    attacks_to_run = ATTACKS
    if args.attack:
        attacks_to_run = [a for a in ATTACKS if a.attack_id == args.attack]
    if args.category:
        attacks_to_run = [a for a in ATTACKS if a.category.lower() == args.category.lower()]

    runner = AttackRunner(attacks_to_run)
    
    if args.baseline or args.command == "benchmark":
        results = await runner.run_all_baselines()
    else:
        # Just run VILR
        res = await runner.run_baseline("VILR")
        results = {"VILR": res}
        for r in res:
            print(f"{r.attack_id}: {r.outcome.value}")

    reporter = Reporter(results)
    if args.json:
        reporter.generate_json(args.json)
    
    # Always generate benchmark
    reporter.generate_markdown("docs/security-benchmark.md")
    print("Report generated at docs/security-benchmark.md")

if __name__ == "__main__":
    asyncio.run(main())
