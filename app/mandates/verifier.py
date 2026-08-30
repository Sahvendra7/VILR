import jwt
from typing import Dict, Any
from app.domain.models import (
    OpenCheckoutMandate, OpenPaymentMandate, 
    ClosedCheckoutMandate, ClosedPaymentMandate
)
from app.domain.errors import InvalidSignature, MandateExpired, HashMismatch, InvalidRequest
from app.domain.interfaces import MandateVerifier
from app.security.crypto import jwk_to_public_key

class VILRMandateVerifier(MandateVerifier):
    def __init__(self, clock_tolerance: int = 30):
        """
        clock_tolerance: seconds of leeway for iat and exp checks.
        """
        self.clock_tolerance = clock_tolerance

    def _verify_jwt(self, token: str, jwk_dict: dict) -> Dict[str, Any]:
        """
        Base verification: decodes JWT using ES256 exclusively, enforcing iat and exp.
        Maps crypto errors to domain exceptions.
        """
        try:
            public_key = jwk_to_public_key(jwk_dict)
        except ValueError as e:
            raise InvalidRequest(f"Invalid JWK: {e}")

        options = {
            "require": ["exp", "iat"],
            "verify_exp": True,
            "verify_iat": True,
            "leeway": self.clock_tolerance,
        }

        try:
            # algorithms=["ES256"] explicitly prevents algorithm confusion attacks
            payload = jwt.decode(token, public_key, algorithms=["ES256"], options=options)
            return payload
        except jwt.ExpiredSignatureError:
            raise MandateExpired("The mandate has expired")
        except jwt.InvalidSignatureError:
            raise InvalidSignature("The mandate signature is invalid")
        except jwt.MissingRequiredClaimError as e:
            raise InvalidRequest(f"Missing required claim: {e}")
        except jwt.DecodeError as e:
            raise InvalidSignature(f"Token decode error: {e}")
        except Exception as e:
            raise InvalidSignature(f"Cryptographic failure: {e}")

    async def verify_open_checkout_mandate(self, token: str, user_public_key: dict) -> OpenCheckoutMandate:
        payload = self._verify_jwt(token, user_public_key)
        
        # Validate typed fields
        try:
            return OpenCheckoutMandate(
                mandate_id=payload["mandate_id"],
                user_id=payload["sub"],
                constraints=payload["constraints"],
                intent_hash=payload["intent_hash"],
                signature=token.split('.')[-1]
            )
        except Exception as e:
            raise InvalidRequest(f"Malformed open checkout mandate: {e}")

    async def verify_closed_checkout_mandate(self, token: str, merchant_public_key: dict) -> ClosedCheckoutMandate:
        payload = self._verify_jwt(token, merchant_public_key)
        
        try:
            return ClosedCheckoutMandate(
                mandate_id=payload["mandate_id"],
                open_mandate_hash=payload["open_mandate_hash"],
                merchant_id=payload["iss"],
                cart_hash=payload["cart_hash"],
                signature=token.split('.')[-1]
            )
        except Exception as e:
            raise InvalidRequest(f"Malformed closed checkout mandate: {e}")
            
    # Open/Closed payment verifications can be added here mirroring the above.
