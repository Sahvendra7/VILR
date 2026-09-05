from typing import List
from datetime import datetime
from app.domain.models import RiskFactor, RiskAssessment

RISK_WEIGHTS = {
    "SIGNATURE_FAILURE": 100,
    "CART_MISMATCH": 80,
    "POLICY_VIOLATION": 70,
    "INTENT_MISMATCH": 50,
    "REPLAY_DETECTED": 100,
    "SEMANTIC_FAIL": 60,
    "SEMANTIC_REVIEW": 30,
    "MANDATE_EXPIRED": 90,
    "MERCHANT_PROHIBITED": 90,
    "CATEGORY_PROHIBITED": 75,
    "PAYMENT_UNKNOWN": 40,
    "PROVIDER_ANOMALY": 40
}

class DeterministicRiskCalculator:
    def calculate_risk(self, signals: List[str]) -> RiskAssessment:
        # Deduplicate signals
        unique_signals = []
        for s in signals:
            if s not in unique_signals:
                unique_signals.append(s)

        factors = []
        score = 0
        for signal in unique_signals:
            if signal in RISK_WEIGHTS:
                weight = RISK_WEIGHTS[signal]
                score += weight
                factors.append(RiskFactor(signal=signal, weight=weight, description=f"Deterministic risk penalty for {signal}"))

        # clamp to 200 max
        score = min(score, 200)

        if score >= 100:
            level = "CRITICAL"
        elif score >= 70:
            level = "HIGH"
        elif score >= 40:
            level = "MEDIUM"
        else:
            level = "LOW"

        return RiskAssessment(
            score=score,
            level=level,
            factors=factors,
            calculated_at=datetime.now()
        )
