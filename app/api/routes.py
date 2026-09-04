from fastapi import APIRouter, HTTPException, status, Depends
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
    records = await gateway.audit.list_by_transaction(transaction_id)
    return {"transaction_id": transaction_id, "records": [r.model_dump() for r in records]}

@router.get("/audit/{transaction_id}/verify")
async def verify_audit_chain(transaction_id: str, gateway = Depends(get_gateway)):
    return await gateway.audit.verify_chain(transaction_id)

@router.get("/metrics")
async def get_metrics():
    return {"status": "ok"}
