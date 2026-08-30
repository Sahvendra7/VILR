import asyncio
import httpx
import time
import traceback
from typing import List, Dict
from app.main import app
from simulator.models import AttackDefinition, AttackResult, AttackOutcome, ExecutionResult
from simulator.baselines import get_baseline_gateway

class AttackRunner:
    def __init__(self, attacks: List[AttackDefinition]):
        self.attacks = attacks

    async def run_baseline(self, baseline_name: str) -> List[AttackResult]:
        results = []
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
            for attack in self.attacks:
                async with app.router.lifespan_context(app) as state:
                    original_gateway = app.state.gateway
                    app.state.gateway = get_baseline_gateway(baseline_name, original_gateway)
                    
                    # Reset mock provider call count if accessible
                    mock_provider = app.state.gateway.payment_executor.provider
                    if hasattr(mock_provider, 'payment_call_count'):
                        mock_provider.payment_call_count = 0
                    if hasattr(mock_provider, 'payment_creation_count'):
                        mock_provider.payment_creation_count = 0
                    
                    start_time = time.time()
                    try:
                        exec_result = await attack.execute(client)
                        duration_ms = (time.time() - start_time) * 1000
                        
                        calls = getattr(mock_provider, 'payment_call_count', 0)
                        creations = getattr(mock_provider, 'payment_creation_count', 0)
                        
                        results.append(
                            AttackResult(
                                attack_id=attack.attack_id,
                                name=attack.name,
                                category=attack.category,
                                outcome=exec_result.outcome,
                                expected=attack.expected_result,
                                defense_layer=attack.defense_layer,
                                severity=attack.severity,
                                http_status=exec_result.http_status,
                                payment_call_count=calls,
                                payment_creation_count=creations,
                                transaction_id=exec_result.transaction_id,
                                evidence=exec_result.evidence,
                                actual=exec_result.outcome.value,
                                duration_ms=duration_ms,
                                error=exec_result.error
                            )
                        )
                    except Exception as e:
                        duration_ms = (time.time() - start_time) * 1000
                        calls = getattr(mock_provider, 'payment_call_count', 0)
                        creations = getattr(mock_provider, 'payment_creation_count', 0)
                        print(f"Error in {attack.attack_id}: {traceback.format_exc()}")
                        results.append(
                            AttackResult(
                                attack_id=attack.attack_id,
                                name=attack.name,
                                category=attack.category,
                                outcome=AttackOutcome.ERROR,
                                expected=attack.expected_result,
                                defense_layer=attack.defense_layer,
                                severity=attack.severity,
                                http_status=500,
                                payment_call_count=calls,
                                payment_creation_count=creations,
                                transaction_id="",
                                evidence="",
                                actual="ERROR",
                                duration_ms=duration_ms,
                                error=str(e),
                                details=traceback.format_exc()
                            )
                        )
                    
                    app.state.gateway = original_gateway
        return results

    async def run_all_baselines(self) -> Dict[str, List[AttackResult]]:
        baselines = ["Baseline_A", "Baseline_B", "Baseline_C", "VILR"]
        all_results = {}
        for b in baselines:
            print(f"Running against {b}...")
            all_results[b] = await self.run_baseline(b)
        return all_results
