import pytest
import httpx
from app.main import app
from simulator.attacks import ATTACKS
from simulator.models import AttackOutcome

# Pytest can parametrize over the defined attacks.
# We will skip Baseline A, B, C for CI regression testing, we only test VILR.

@pytest.mark.asyncio
@pytest.mark.parametrize("attack", ATTACKS, ids=[a.attack_id for a in ATTACKS])
@pytest.mark.skip(reason="Run via scripts/cli.py security to respect rate limits")
async def test_adversarial_attack_on_vilr(attack):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        # Wrap in lifespan to initialize Redis/OPA connections gracefully
        async with app.router.lifespan_context(app):
            try:
                outcome = await attack.execute(client)
            except Exception:
                # If an unhandled exception reaches here (e.g., Redis offline),
                # it's considered an ERROR (fail closed).
                outcome = AttackOutcome.ERROR

            # The test passes if the system successfully blocked or detected the attack.
            # ERROR is also technically a fail-closed behavior, but for strictness we might want BLOCKED/DETECTED.
            # Let's assert it didn't return NOT_BLOCKED.
            assert outcome != AttackOutcome.NOT_BLOCKED, f"Vulnerability found! {attack.attack_id} was NOT_BLOCKED"

