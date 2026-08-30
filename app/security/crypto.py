import rfc8785
import hashlib
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from app.domain.models import Cart

def generate_p256_keypair():
    """Generates an ECDSA P-256 keypair."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    return private_key, public_key

def b64url_encode(data: bytes) -> str:
    """Base64URL encode with no padding."""
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

def b64url_decode(s: str) -> bytes:
    """Base64URL decode with padding correction."""
    s += '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s)

def public_key_to_jwk(public_key: ec.EllipticCurvePublicKey) -> dict:
    """Converts a P-256 public key to JWK representation."""
    if not isinstance(public_key.curve, ec.SECP256R1):
        raise ValueError("Only P-256 curve is supported")
        
    public_numbers = public_key.public_numbers()
    x = public_numbers.x.to_bytes(32, byteorder='big')
    y = public_numbers.y.to_bytes(32, byteorder='big')
    
    return {
        "kty": "EC",
        "crv": "P-256",
        "x": b64url_encode(x),
        "y": b64url_encode(y)
    }

def jwk_to_public_key(jwk_dict: dict) -> ec.EllipticCurvePublicKey:
    """Converts a JWK representation to a P-256 public key."""
    if jwk_dict.get("kty") != "EC" or jwk_dict.get("crv") != "P-256":
        raise ValueError("Only P-256 EC keys supported")
        
    x = int.from_bytes(b64url_decode(jwk_dict["x"]), byteorder='big')
    y = int.from_bytes(b64url_decode(jwk_dict["y"]), byteorder='big')
    
    return ec.EllipticCurvePublicNumbers(x, y, ec.SECP256R1()).public_key()

def compute_jcs_hash(payload: dict) -> str:
    """
    Computes RFC 8785 JSON Canonicalization Scheme (JCS) hash.
    payload -> JCS bytes -> SHA-256 -> Base64URL
    """
    canonical_bytes = rfc8785.dumps(payload)
    digest = hashlib.sha256(canonical_bytes).digest()
    return b64url_encode(digest)

def compute_checkout_hash(cart: Cart) -> str:
    """
    Computes a deterministic hash of the integrity-bound fields of a Cart.
    """
    payload = {
        "merchant_id": cart.merchant_id,
        "currency": cart.currency,
        "total_amount": str(cart.total_amount),
        "items": [
            {
                "item_id": item.item_id,
                "quantity": item.quantity,
                "unit_price": str(item.unit_price),
                "currency": item.currency
            } for item in cart.items
        ]
    }
    return compute_jcs_hash(payload)

def compute_open_mandate_hash(payload: dict) -> str:
    """
    Computes the hash of an Open Mandate's integrity-bound fields.
    """
    return compute_jcs_hash(payload)
