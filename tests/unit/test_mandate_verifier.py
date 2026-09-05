import pytest
import time
from app.mandates.verifier import VILRMandateVerifier
from app.security.signer import LocalSigner
from app.security.crypto import generate_p256_keypair
from app.domain.errors import MandateExpired, InvalidSignature, InvalidRequest

@pytest.fixture
def user_keys():
    return generate_p256_keypair()

@pytest.fixture
def merchant_keys():
    return generate_p256_keypair()

@pytest.mark.asyncio
async def test_verify_open_checkout_mandate(user_keys):
    priv, pub = user_keys
    signer = LocalSigner(priv)
    jwk = signer.get_public_key_jwk()

    now = int(time.time())
    payload = {
        "sub": "u1",
        "iss": "u1",
        "iat": now,
        "exp": now + 3600,
        "mandate_id": "m1",
        "constraints": {
            "max_budget": "100.00",
            "currency": "USD",
            "allowed_merchants": [],
            "allowed_categories": [],
            "prohibited_merchants": [],
            "prohibited_categories": []
        },
        "intent_hash": "hash123"
    }

    token = signer.sign(payload)
    verifier = VILRMandateVerifier()

    mandate = await verifier.verify_open_checkout_mandate(token, jwk)
    assert mandate.mandate_id == "m1"

@pytest.mark.asyncio
async def test_expired_mandate(user_keys):
    priv, _ = user_keys
    signer = LocalSigner(priv)
    jwk = signer.get_public_key_jwk()

    # Token expired 1 hour ago
    now = int(time.time()) - 3600
    payload = {
        "sub": "u1",
        "iss": "u1",
        "iat": now - 3600,
        "exp": now,
        "mandate_id": "m1",
        "constraints": {"max_budget": "100.00", "currency": "USD"},
        "intent_hash": "hash123"
    }

    token = signer.sign(payload)
    verifier = VILRMandateVerifier(clock_tolerance=0)

    with pytest.raises(MandateExpired):
        await verifier.verify_open_checkout_mandate(token, jwk)

@pytest.mark.asyncio
async def test_wrong_signer_key(user_keys, merchant_keys):
    user_priv, _ = user_keys
    _, merchant_pub = merchant_keys

    signer = LocalSigner(user_priv) # Signed by user

    # But try to verify with merchant key
    from app.security.crypto import public_key_to_jwk
    merchant_jwk = public_key_to_jwk(merchant_pub)

    now = int(time.time())
    payload = {
        "sub": "u1", "iat": now, "exp": now + 3600,
        "mandate_id": "m1",
        "constraints": {"max_budget": "100.00", "currency": "USD"},
        "intent_hash": "hash123"
    }
    token = signer.sign(payload)
    verifier = VILRMandateVerifier()

    with pytest.raises(InvalidSignature):
        await verifier.verify_open_checkout_mandate(token, merchant_jwk)

@pytest.mark.asyncio
async def test_modified_jwt(user_keys):
    priv, _ = user_keys
    signer = LocalSigner(priv)
    jwk = signer.get_public_key_jwk()

    now = int(time.time())
    payload = {
        "sub": "u1", "iat": now, "exp": now + 3600,
        "mandate_id": "m1",
        "constraints": {"max_budget": "100.00", "currency": "USD"},
        "intent_hash": "hash123"
    }
    token = signer.sign(payload)

    # Tamper token (change payload part)
    header, pl, sig = token.split('.')
    import base64
    # decode, modify, re-encode
    pl_dec = base64.urlsafe_b64decode(pl + "===").decode()
    pl_dec = pl_dec.replace("100.00", "999.00")
    pl_mod = base64.urlsafe_b64encode(pl_dec.encode()).decode().rstrip('=')

    tampered_token = f"{header}.{pl_mod}.{sig}"
    verifier = VILRMandateVerifier()

    with pytest.raises(InvalidSignature):
        await verifier.verify_open_checkout_mandate(tampered_token, jwk)

@pytest.mark.asyncio
async def test_verify_closed_checkout_mandate(merchant_keys):
    priv, pub = merchant_keys
    signer = LocalSigner(priv)
    jwk = signer.get_public_key_jwk()

    now = int(time.time())
    payload = {
        "sub": "u1", "iss": "m1", "iat": now, "exp": now + 3600,
        "mandate_id": "c1",
        "open_mandate_hash": "open123",
        "cart_hash": "cart123"
    }

    token = signer.sign(payload)
    verifier = VILRMandateVerifier()

    mandate = await verifier.verify_closed_checkout_mandate(token, jwk)
    assert mandate.mandate_id == "c1"
    assert mandate.open_mandate_hash == "open123"

@pytest.mark.asyncio
async def test_verify_malformed_closed_checkout(merchant_keys):
    priv, pub = merchant_keys
    signer = LocalSigner(priv)
    jwk = signer.get_public_key_jwk()

    now = int(time.time())
    payload = {
        "sub": "u1", "iss": "m1", "iat": now, "exp": now + 3600,
        "mandate_id": "c1",
        # Missing open_mandate_hash and cart_hash
    }

    token = signer.sign(payload)
    verifier = VILRMandateVerifier()

    with pytest.raises(InvalidRequest):
        await verifier.verify_closed_checkout_mandate(token, jwk)
