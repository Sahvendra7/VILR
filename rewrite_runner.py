import re

with open('simulator/runner.py', 'r') as f:
    content = f.read()

content = content.replace(
    'from simulator.models import AttackDefinition, AttackResult, AttackOutcome, ExecutionResult',
    'from simulator.models import AttackDefinition, AttackResult, AttackOutcome, ExecutionResult, DecisionOutcome, SideEffectOutcome'
)

# Modify AttackResult creation inside the try block
replacement_try = """
                        calls = getattr(mock_provider, 'payment_call_count', 0)
                        creations = getattr(mock_provider, 'payment_creation_count', 0)
                        
                        actual_side_effect = exec_result.actual_side_effect
                        if creations > 0:
                            actual_side_effect = SideEffectOutcome.PAYMENT_EXECUTED
                        elif actual_side_effect == SideEffectOutcome.UNKNOWN and calls > 0:
                            actual_side_effect = SideEffectOutcome.PAYMENT_EXECUTED
                        elif actual_side_effect == SideEffectOutcome.UNKNOWN:
                            actual_side_effect = SideEffectOutcome.NONE

                        status = "PASS" if exec_result.actual_decision == attack.expected_decision and actual_side_effect == attack.expected_side_effect else "FAIL"
                        
                        results.append(
                            AttackResult(
                                case_id=attack.attack_id,
                                name=attack.name,
                                category=attack.category,
                                expected_decision=attack.expected_decision,
                                actual_decision=exec_result.actual_decision,
                                expected_side_effect=attack.expected_side_effect,
                                actual_side_effect=actual_side_effect,
                                status=status,
                                outcome=exec_result.outcome,
                                expected=attack.expected_result,
                                defense_layer=attack.defense_layer,
                                severity=attack.severity,
                                http_status=exec_result.http_status,
                                payment_call_count=calls,
                                payment_creation_count=creations,
                                transaction_id=exec_result.transaction_id,
                                evidence=exec_result.evidence,
                                actual=exec_result.outcome.value if exec_result.outcome else "",
                                duration_ms=duration_ms,
                                error=exec_result.error
                            )
                        )
"""
content = re.sub(
    r"calls = getattr\(mock_provider, 'payment_call_count', 0\).*?error=exec_result\.error\n\s*\)\n\s*\)",
    replacement_try,
    content,
    flags=re.DOTALL
)

replacement_except = """
                        print(f"Error in {attack.attack_id}: {traceback.format_exc()}")
                        results.append(
                            AttackResult(
                                case_id=attack.attack_id,
                                name=attack.name,
                                category=attack.category,
                                expected_decision=attack.expected_decision,
                                actual_decision=DecisionOutcome.ERROR,
                                expected_side_effect=attack.expected_side_effect,
                                actual_side_effect=SideEffectOutcome.NONE,
                                status="FAIL",
                                error_type="Exception",
                                explanation=str(e),
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
"""
content = re.sub(
    r"print\(f\"Error in \{attack\.attack_id\}: \{traceback\.format_exc\(\)\}\"\).*?details=traceback\.format_exc\(\)\n\s*\)\n\s*\)",
    replacement_except,
    content,
    flags=re.DOTALL
)

with open('simulator/runner.py', 'w') as f:
    f.write(content)
