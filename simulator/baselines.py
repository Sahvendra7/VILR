from app.domain.gateway import GatewayOrchestrator, GatewayAuthorizeRequest, GatewayExecuteRequest
from app.domain.state_machine import StateController, TransactionState
from typing import Dict, Any

class BaselineCGateway(GatewayOrchestrator):
    """
    Baseline C: AP2-compatible crypto only.
    Checks signatures, but bypasses Semantic Verifier and OPA Policy.
    """
    async def authorize(self, request: GatewayAuthorizeRequest) -> dict:
        try:
            await self.verifier.verify_open_checkout_mandate(request.open_checkout_token, request.user_public_key)
            await self.verifier.verify_closed_checkout_mandate(request.closed_checkout_token, request.merchant_public_key)
        except Exception as e:
            raise e
        # Bypass Semantic and Policy
        return {"status": "AUTHORIZED", "execution_token": "token_c", "transaction_id": request.transaction_id}
        
    async def execute(self, request: GatewayExecuteRequest) -> dict:
        return {"status": "CONFIRMED", "transaction_id": request.transaction_id}

class BaselineBGateway(GatewayOrchestrator):
    """
    Baseline B: Agent + simple amount policy.
    Bypasses Crypto and Semantic verification. Checks budget limits directly.
    """
    async def authorize(self, request: GatewayAuthorizeRequest) -> dict:
        # Bypass Crypto and Semantic
        try:
            budget = float(request.user_intent.hard_constraints.max_budget)
            if float(request.cart.total_amount) > budget:
                raise Exception("Over budget")
        except Exception as e:
            raise e
        return {"status": "AUTHORIZED", "execution_token": "token_b", "transaction_id": request.transaction_id}
        
    async def execute(self, request: GatewayExecuteRequest) -> dict:
        return {"status": "CONFIRMED", "transaction_id": request.transaction_id}

class BaselineAGateway(GatewayOrchestrator):
    """
    Baseline A: LLM agent + direct payment access.
    Blindly trusts input. Bypasses Crypto, Semantic, Policy.
    """
    async def authorize(self, request: GatewayAuthorizeRequest) -> dict:
        return {"status": "AUTHORIZED", "execution_token": "token_a", "transaction_id": request.transaction_id}
        
    async def execute(self, request: GatewayExecuteRequest) -> dict:
        return {"status": "CONFIRMED", "transaction_id": request.transaction_id}

def get_baseline_gateway(name: str, original_gateway: GatewayOrchestrator) -> GatewayOrchestrator:
    if name == "VILR":
        return original_gateway
    elif name == "Baseline_C":
        return BaselineCGateway(original_gateway.verifier, original_gateway.idempotency, original_gateway.semantic, original_gateway.policy, original_gateway.payment_executor, original_gateway.audit)
    elif name == "Baseline_B":
        return BaselineBGateway(original_gateway.verifier, original_gateway.idempotency, original_gateway.semantic, original_gateway.policy, original_gateway.payment_executor, original_gateway.audit)
    elif name == "Baseline_A":
        return BaselineAGateway(original_gateway.verifier, original_gateway.idempotency, original_gateway.semantic, original_gateway.policy, original_gateway.payment_executor, original_gateway.audit)
    raise ValueError(f"Unknown baseline {name}")
