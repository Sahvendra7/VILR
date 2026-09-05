with open("app/domain/gateway.py", "r") as f:
    content = f.read()

content = content.replace("from app.domain.errors import (", "from app.domain.errors import (\n    PolicyViolation,")

# Add transition to POLICY_EVALUATED before checking decision.allowed
content = content.replace('context["policy_decision"] = "ALLOW" if decision.allowed else "DENY"', 'context["policy_decision"] = "ALLOW" if decision.allowed else "DENY"\n            state.transition_to(TransactionState.POLICY_EVALUATED)\n            await self._log(tx_id, TransactionState.POLICY_EVALUATED, **context)')

with open("app/domain/gateway.py", "w") as f:
    f.write(content)
