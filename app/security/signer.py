import jwt
from typing import Protocol, Dict, Any
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey
from app.security.crypto import public_key_to_jwk

class Signer(Protocol):
    def sign(self, payload: Dict[str, Any]) -> str:
        ...

    def get_public_key_jwk(self) -> Dict[str, Any]:
        ...

class LocalSigner:
    """
    A local signer for development and prototype use.
    Uses ES256 (ECDSA P-256 + SHA-256).
    """
    def __init__(self, private_key: EllipticCurvePrivateKey):
        self._private_key = private_key
        self._public_key = private_key.public_key()

    def sign(self, payload: Dict[str, Any]) -> str:
        # We explicitly enforce ES256 algorithm
        return jwt.encode(payload, self._private_key, algorithm="ES256")

    def get_public_key_jwk(self) -> Dict[str, Any]:
        return public_key_to_jwk(self._public_key)
