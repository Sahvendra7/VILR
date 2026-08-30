class VILRError(Exception):
    """Base exception for all VILR application errors."""
    pass

class InvalidStateTransition(VILRError):
    pass

class InvalidRequest(VILRError):
    pass

class MandateExpired(VILRError):
    pass

class InvalidSignature(VILRError):
    pass

class HashMismatch(VILRError):
    pass

class MerchantUntrusted(VILRError):
    pass

class ReplayDetected(VILRError):
    pass

class SemanticDrift(VILRError):
    pass

class PolicyDenied(VILRError):
    pass

class PaymentUnknown(VILRError):
    pass

class DuplicateExecution(VILRError):
    pass

class IdempotencyError(VILRError):
    """Base class for idempotency related errors."""
    pass

class IdempotencyUnavailable(IdempotencyError):
    """Raised when Redis or the idempotency store is unavailable."""
    pass

class IdempotencyOwnershipFailure(IdempotencyError):
    """Raised when an operation is attempted by a non-owner."""
    pass
class PolicyUnavailable(VILRError):
    """Raised when the OPA policy engine is unreachable."""
    pass
