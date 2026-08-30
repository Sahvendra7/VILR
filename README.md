# VILR 2.0 - Verifiable Intent & Transaction Integrity Gateway

VILR is a zero-trust runtime transaction-integrity gateway positioned between AI shopping agents and payment providers.

## Getting Started

```bash
docker compose up -d --build
```

## Implementation Status
* **Phase 0 (Foundation)**: COMPLETE
* **Phase 1 (Domain Models)**: IN PROGRESS

### Phase 7: Real E2E Demo Sequence
1. Start OPA and Redis:
   `docker-compose up -d redis opa`
2. Start the Application:
   `REDIS_URL=redis://localhost:6379/0 OPA_URL=http://localhost:8181 uvicorn app.main:app --reload`
3. Execute Authorize (`/v1/authorize`) -> Execute (`/v1/execute`) -> Query Ledger (`/v1/audit/{tx_id}`) -> Verify Proof (`/v1/audit/{tx_id}/verify`).
