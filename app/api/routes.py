from fastapi import APIRouter, HTTPException, status, Depends
from app.exception.intelligence import ExceptionInvestigation
from app.domain.models import SecurityReceipt
from datetime import datetime
from app.api.schemas import (
    IntentRequest, IntentResponse,
    AuthorizeRequest, AuthorizeResponse,
    ExecuteRequest, ExecuteResponse,
    VerifyRequest, VerifyResponse
)
from app.domain.models import AuditRecord
from app.domain.gateway import GatewayAuthorizeRequest, GatewayExecuteRequest
from app.api.deps import get_gateway

router = APIRouter(prefix="/v1")

from pydantic import BaseModel
from simulator.scenarios import ScenarioGenerator
from decimal import Decimal
from app.domain.models import Cart, CartItem

class DemoPayloadRequest(BaseModel):
    intent: str
    raw_prompt: str
    amount: str
    items: list
    max_budget: str = "70000.00"

@router.post("/demo/generate_payload")
async def generate_demo_payload(req: DemoPayloadRequest):
    generator = ScenarioGenerator()
    c = Cart(
        merchant_id="m1",
        items=[CartItem(**i) for i in req.items],
        total_amount=Decimal(req.amount),
        currency="INR"
    )
    payload = generator.generate_valid_payload({
        "raw_prompt": req.raw_prompt,
        "semantic_intent": req.intent,
        "hard_constraints": {"max_budget": req.max_budget, "currency": "INR"},
        "cart_override": c
    })
    
    import jwt
    payload["open_mandate_hash"] = jwt.decode(payload["closed_checkout_token"], options={"verify_signature": False})["open_mandate_hash"]
    return payload





@router.post("/authorize", response_model=AuthorizeResponse)
async def authorize_transaction(req: AuthorizeRequest, gateway = Depends(get_gateway)):
    auth_req = GatewayAuthorizeRequest(
        transaction_id=req.transaction_id,
        open_checkout_token=req.open_checkout_token,
        closed_checkout_token=req.closed_checkout_token,
        user_intent=req.user_intent,
        cart=req.cart,
        user_public_key=req.user_public_key,
        merchant_public_key=req.merchant_public_key
    )
    result = await gateway.authorize(auth_req)
    return AuthorizeResponse(
        transaction_id=result["transaction_id"],
        status=result["status"],
        message="Authorization successful",
        reservation_status="COMMITTED",
        execution_token=result["execution_token"]
    )

@router.post("/execute", response_model=ExecuteResponse)
async def execute_transaction(req: ExecuteRequest, gateway = Depends(get_gateway)):
    exec_req = GatewayExecuteRequest(**req.model_dump())
    result = await gateway.execute(exec_req)
    return ExecuteResponse(
        transaction_id=result["transaction_id"],
        status=result["status"],
        receipt=result
    )



@router.get("/audit/{transaction_id}")
async def get_audit(transaction_id: str, gateway = Depends(get_gateway)):
    records = await gateway.audit.get_transaction_history(transaction_id) if hasattr(gateway.audit, 'get_transaction_history') else await gateway.audit.list_by_transaction(transaction_id)
    return {"transaction_id": transaction_id, "records": [r.model_dump() for r in records]}

@router.get("/audit/{transaction_id}/verify")
async def verify_audit_chain(transaction_id: str, gateway = Depends(get_gateway)):
    return await gateway.audit.verify_chain(transaction_id)

@router.get("/metrics")
async def get_metrics():
    return {"status": "ok"}

@router.post("/investigate/{transaction_id}", response_model=ExceptionInvestigation)
async def investigate_transaction(
    transaction_id: str,
    gateway=Depends(get_gateway)
):
    try:
        return await gateway.investigate_transaction(transaction_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/receipt/{transaction_id}", response_model=SecurityReceipt)
async def get_receipt(
    transaction_id: str,
    gateway=Depends(get_gateway)
):
    try:
        return await gateway.generate_receipt(transaction_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


import asyncio
@router.post("/demo/concurrency")
async def demo_concurrency(req: ExecuteRequest, gateway = Depends(get_gateway)):
    async def try_exec():
        exec_req = GatewayExecuteRequest(**req.model_dump())
        try:
            return await gateway.execute(exec_req)
        except Exception as e:
            return {"error": str(e), "status": "FAILED"}

    results = await asyncio.gather(*[try_exec() for _ in range(100)])

    successful = len([r for r in results if r.get("status") == "SUCCESS"])
    replays = len([r for r in results if r.get("error")])

    return {
        "attempts": 100,
        "successful_token_consumption": successful,
        "replay_rejected": replays,
        "observed_provider_executions": successful
    }
