import re
with open("app/domain/gateway.py", "r") as f:
    content = f.read()

# Add imports for models
imports = """
from app.domain.models import (
    DecisionEvidence, IntentEvidence, CryptographicEvidence, CartEvidence,
    ReplayEvidence, SemanticEvidence, PolicyEvidence, ExecutionEvidence, PolicyMetadata
)
from app.policy.explainability import DeterministicPolicyExplainer
from datetime import datetime
import hashlib
import json
"""
content = content.replace("from datetime import datetime, UTC", "from datetime import datetime, UTC\n" + imports)

# We will inject the evidence builder into the `evaluate` try/except block.
try_block_old = """
            decision = await self.policy.evaluate(opa_input)
            context["policy_decision"] = "ALLOW" if decision.allowed else "DENY"
            
            if not decision.allowed:
                raise PolicyDenied(f"Policy denied: {decision.violations}")
                
            state.transition_to(TransactionState.POLICY_EVALUATED)
            await self._log(tx_id, TransactionState.POLICY_EVALUATED, **context)
            
        except Exception as e:
            await self.idempotency.release(reservation_key, tx_id)
            if not isinstance(e, PolicyDenied):
                raise
            state.transition_to(TransactionState.POLICY_DENIED)
            context["failure_reason"] = str(e)
            await self._log(tx_id, TransactionState.POLICY_DENIED, **context)
            raise
"""

try_block_new = """
            decision = await self.policy.evaluate(opa_input)
            context["policy_decision"] = "ALLOW" if decision.allowed else "DENY"
            
            # BUILD EVIDENCE
            policy_meta = PolicyMetadata(name="payment_authorization", version=getattr(decision, "policy_version", "unknown"), hash=getattr(decision, "policy_hash", "unknown"))
            explainer = DeterministicPolicyExplainer(policy_meta)
            explanation = explainer.explain(decision, opa_input)
            
            evidence = DecisionEvidence(
                intent=IntentEvidence(
                    intent_id=request.user_intent.user_id,
                    intent_timestamp=datetime.now(),
                    intent_status="VERIFIED",
                    intent_hash=open_mandate.intent_hash
                ),
                cryptographic=CryptographicEvidence(
                    signature_verified=True,
                    intent_hash=open_mandate.intent_hash,
                    cart_hash=closed_mandate.cart_hash,
                    transaction_binding=True,
                    verification_result="SUCCESS"
                ),
                cart=CartEvidence(
                    expected_cart_hash=closed_mandate.cart_hash,
                    actual_cart_hash=actual_cart_hash,
                    cart_match=True,
                    expected_amount=str(request.cart.total_amount),
                    actual_amount=str(request.cart.total_amount)
                ),
                replay=ReplayEvidence(
                    idempotency_key=reservation_key,
                    replay_detected=False,
                    reservation_status="ACQUIRED",
                    execution_token_status="PENDING"
                ),
                semantic=SemanticEvidence(
                    semantic_result=sem_result.status,
                    confidence=sem_result.confidence,
                    detected_mismatches=[],
                    provider="GeminiLLMProvider",
                    advisory_only=True
                ) if sem_result else None,
                policy=PolicyEvidence(
                    policy_name=policy_meta.name,
                    policy_version=policy_meta.version,
                    policy_hash=policy_meta.hash,
                    policy_decision="ALLOW" if decision.allowed else "DENY",
                    matched_rules=[],
                    violations=decision.violations
                ),
                execution=ExecutionEvidence(
                    execution_authorized=decision.allowed,
                    provider="Razorpay",
                    provider_request_id=None,
                    execution_status="NOT_REACHED"
                )
            )
            
            evidence_dict = evidence.model_dump(mode='json')
            canon_str = json.dumps(evidence_dict, separators=(',', ':'), sort_keys=True)
            evidence.evidence_hash = hashlib.sha256(canon_str.encode('utf-8')).hexdigest()
            evidence_dict["evidence_hash"] = evidence.evidence_hash
            
            context["evidence"] = evidence_dict
            context["explanation"] = explanation.model_dump(mode='json')
            context["policy_version"] = policy_meta.version
            
            if not decision.allowed:
                raise PolicyDenied(f"Policy denied: {decision.violations}")
                
            state.transition_to(TransactionState.POLICY_EVALUATED)
            await self._log(tx_id, TransactionState.POLICY_EVALUATED, **context)
            
        except Exception as e:
            await self.idempotency.release(reservation_key, tx_id)
            if not isinstance(e, PolicyDenied):
                raise
            state.transition_to(TransactionState.POLICY_DENIED)
            context["failure_reason"] = str(e)
            await self._log(tx_id, TransactionState.POLICY_DENIED, **context)
            raise
"""

content = content.replace(try_block_old, try_block_new)

with open("app/domain/gateway.py", "w") as f:
    f.write(content)
