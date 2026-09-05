import httpx
import redis.asyncio as redis
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from app.config.settings import settings
from app.api.routes import router as v1_router
from contextlib import asynccontextmanager

from app.mandates.verifier import VILRMandateVerifier
from app.idempotency.store import RedisIdempotencyStore
from app.semantic.provider import get_provider
from app.semantic.verifier import AISemanticVerifier
from app.policy.engine import OPAPolicyEngine
from app.execution.executor import PaymentExecutor
from adapters.razorpay.provider import MockRazorpayProvider
from app.audit.ledger import MemoryAuditLedger
from app.domain.gateway import GatewayOrchestrator
from app.exception.intelligence import ExceptionIntelligenceLayer
from app.domain.errors import (
    VILRError, InvalidStateTransition, InvalidRequest, MandateExpired,
    InvalidSignature, HashMismatch, MerchantUntrusted, ReplayDetected,
    SemanticDrift, PolicyDenied, PaymentUnknown, DuplicateExecution
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_client = redis.from_url(settings.redis_url)

    verifier = VILRMandateVerifier()
    idempotency = RedisIdempotencyStore(redis_client)
    semantic_provider = get_provider(settings.llm_provider, api_key=settings.gemini_api_key, model=settings.gemini_model)
    semantic = AISemanticVerifier(semantic_provider)
    policy = OPAPolicyEngine(opa_url=settings.opa_url)
    provider = MockRazorpayProvider()
    executor = PaymentExecutor(provider)
    if settings.supabase_url and settings.supabase_key:
        from app.audit.supabase_ledger import SupabaseAuditLedger
        audit = SupabaseAuditLedger()
    else:
        audit = MemoryAuditLedger()

    exception_intelligence = ExceptionIntelligenceLayer(semantic_provider)

    app.state.gateway = GatewayOrchestrator(
        verifier=verifier,
        idempotency=idempotency,
        semantic=semantic,
        policy=policy,
        payment_executor=executor,
        audit=audit,
        exception_intelligence=exception_intelligence
    )
    yield
    await redis_client.close()

app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.include_router(v1_router)
app.mount("/dashboard", StaticFiles(directory="static", html=True), name="static")

# Exception Handlers
@app.exception_handler(InvalidStateTransition)
async def handle_invalid_state_transition(request: Request, exc: InvalidStateTransition):
    return JSONResponse(status_code=409, content={"error": "InvalidStateTransition", "message": str(exc), "code": "STATE_CONFLICT"})

@app.exception_handler(PolicyDenied)
async def handle_policy_denied(request: Request, exc: PolicyDenied):
    return JSONResponse(status_code=403, content={"error": "PolicyDenied", "message": str(exc), "code": "FORBIDDEN_POLICY"})

@app.exception_handler(ReplayDetected)
async def handle_replay_detected(request: Request, exc: ReplayDetected):
    return JSONResponse(status_code=409, content={"error": "ReplayDetected", "message": str(exc), "code": "REPLAY_DETECTED"})

@app.exception_handler(DuplicateExecution)
async def handle_duplicate_execution(request: Request, exc: DuplicateExecution):
    return JSONResponse(status_code=409, content={"error": "DuplicateExecution", "message": str(exc), "code": "DUPLICATE_EXECUTION"})

@app.exception_handler(InvalidSignature)
async def handle_invalid_signature(request: Request, exc: InvalidSignature):
    return JSONResponse(status_code=401, content={"error": "InvalidSignature", "message": str(exc), "code": "INVALID_SIGNATURE"})

@app.exception_handler(HashMismatch)
async def handle_hash_mismatch(request: Request, exc: HashMismatch):
    return JSONResponse(status_code=400, content={"error": "HashMismatch", "message": str(exc), "code": "HASH_MISMATCH"})

@app.exception_handler(MerchantUntrusted)
async def handle_merchant_untrusted(request: Request, exc: MerchantUntrusted):
    return JSONResponse(status_code=403, content={"error": "MerchantUntrusted", "message": str(exc), "code": "MERCHANT_UNTRUSTED"})

@app.exception_handler(MandateExpired)
async def handle_mandate_expired(request: Request, exc: MandateExpired):
    return JSONResponse(status_code=400, content={"error": "MandateExpired", "message": str(exc), "code": "MANDATE_EXPIRED"})

@app.exception_handler(SemanticDrift)
async def handle_semantic_drift(request: Request, exc: SemanticDrift):
    return JSONResponse(status_code=400, content={"error": "SemanticDrift", "message": str(exc), "code": "SEMANTIC_DRIFT"})

@app.exception_handler(PaymentUnknown)
async def handle_payment_unknown(request: Request, exc: PaymentUnknown):
    return JSONResponse(status_code=502, content={"error": "PaymentUnknown", "message": str(exc), "code": "PAYMENT_UNKNOWN_STATE"})

@app.exception_handler(VILRError)
async def handle_vilr_error(request: Request, exc: VILRError):
    return JSONResponse(status_code=400, content={"error": "VILRError", "message": str(exc), "code": "BAD_REQUEST"})

@app.get("/health")
async def health_check():
    redis_status = "ok"
    try:
        r = redis.from_url(settings.redis_url)
        await r.ping()
        await r.close()
    except Exception as e:
        redis_status = "unavailable"

    opa_status = "ok"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{settings.opa_url}/health")
            resp.raise_for_status()
    except Exception as e:
        opa_status = "unavailable"

    return {
        "status": "ok",
        "redis": redis_status,
        "opa": opa_status
    }
