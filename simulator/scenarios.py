import time
from uuid import uuid4
from decimal import Decimal
from app.security.crypto import generate_p256_keypair, compute_open_mandate_hash, compute_checkout_hash
from app.security.signer import LocalSigner
from app.domain.models import Cart, CartItem

class ScenarioGenerator:
    def __init__(self):
        self.user_priv, self.user_pub = generate_p256_keypair()
        self.user_signer = LocalSigner(self.user_priv)
        
        self.merchant_priv, self.merchant_pub = generate_p256_keypair()
        self.merchant_signer = LocalSigner(self.merchant_priv)
        
    def generate_valid_payload(self, overrides=None):
        """Generates a fully valid VILR /v1/authorize payload."""
        overrides = overrides or {}
        tx_id = overrides.get("transaction_id", f"tx_{uuid4().hex}")
        
        # User Intent
        user_id = overrides.get("user_id", "u123")
        intent = {
            "user_id": user_id,
            "raw_prompt": overrides.get("raw_prompt", "Buy a laptop under 50000"),
            "semantic_intent": overrides.get("semantic_intent", "laptop"),
            "hard_constraints": overrides.get("hard_constraints", {"max_budget": "50000", "currency": "INR"}),
            "soft_preferences": {}
        }
        
        # Open Mandate (Signed by User)
        now = int(time.time())
        open_mandate_payload = {
            "iss": user_id,
            "sub": user_id,
            "iat": now,
            "exp": now + 3600,
            "mandate_id": f"m_open_{uuid4().hex}",
            "intent_hash": "mock_intent_hash",
            "constraints": intent["hard_constraints"]
        }
        
        if "open_mandate_override" in overrides:
            open_mandate_payload.update(overrides["open_mandate_override"])
            
        open_token = self.user_signer.sign(open_mandate_payload)
        
        # Cart
        merchant_id = overrides.get("merchant_id", "m456")
        cart = Cart(
            merchant_id=merchant_id,
            currency="INR",
            total_amount=Decimal(overrides.get("total_amount", "45000.00")),
            items=[
                CartItem(
                    item_id="item_1",
                    quantity=1,
                    unit_price=Decimal(overrides.get("total_amount", "45000.00")),
                    currency="INR",
                    name="Laptop",
                    category="Electronics",
                    description=overrides.get("merchant_description", "Lenovo ThinkPad")
                )
            ]
        )
        if "cart_override" in overrides:
            cart = overrides["cart_override"]
            
        cart_hash = compute_checkout_hash(cart)
        open_hash = compute_open_mandate_hash(open_mandate_payload)
        
        # Closed Mandate (Signed by Merchant)
        closed_mandate_payload = {
            "iss": merchant_id,
            "sub": merchant_id,
            "iat": now,
            "exp": now + 3600,
            "mandate_id": f"m_closed_{uuid4().hex}",
            "open_mandate_hash": open_hash,
            "cart_hash": cart_hash
        }
        if "closed_mandate_override" in overrides:
            closed_mandate_payload.update(overrides["closed_mandate_override"])
            
        closed_token = self.merchant_signer.sign(closed_mandate_payload)
        
        # Fabricate the final payload
        payload = {
            "transaction_id": tx_id,
            "open_checkout_token": open_token,
            "closed_checkout_token": closed_token,
            "user_intent": intent,
            "cart": cart.model_dump(mode='json'),
            "user_public_key": self.user_signer.get_public_key_jwk(),
            "merchant_public_key": self.merchant_signer.get_public_key_jwk()
        }
        
        if "payload_override" in overrides:
            payload.update(overrides["payload_override"])
            
        return payload
