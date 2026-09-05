import httpx

import hashlib
import os

def get_policy_metadata() -> dict:
    path = "policies/authorization.rego"
    if not os.path.exists(path):
        return {"name": "payment_authorization", "version": "unknown", "hash": "unknown"}
    with open(path, "rb") as f:
        content = f.read()
    h = hashlib.sha256(content).hexdigest()
    # Read version from file (e.g. policy_version := "v1")
    version = "unknown"
    for line in content.decode("utf-8").splitlines():
        if "policy_version :=" in line:
            version = line.split(":=")[1].strip().strip('"')
            break
    return {"name": "payment_authorization", "version": version, "hash": h}

from typing import Dict, Any
import structlog
from app.domain.interfaces import PolicyEngine
from app.domain.models import AuthorizationDecision
from app.domain.errors import PolicyUnavailable

logger = structlog.get_logger(__name__)

class OPAPolicyEngine(PolicyEngine):
    def __init__(self, opa_url: str, timeout: float = 2.0):
        self.opa_url = opa_url
        self.timeout = timeout
        self.decision_endpoint = f"{self.opa_url}/v1/data/vilr/authorization/decision"

    async def evaluate(self, input_data: Dict[str, Any]) -> AuthorizationDecision:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.decision_endpoint,
                    json={"input": input_data}
                )
                response.raise_for_status()
                # OPA wraps the return in a "result" key
                response_json = response.json()
                result = response_json.get("result", {})
                
                # If the policy evaluated successfully but result is empty, it means default deny
                if not result:
                    result = {"allow": False, "violations": [{"code": "POLICY_DEFAULT_DENY", "message": "Policy engine returned no decision"}], "policy_version": "unknown"}
                
                return AuthorizationDecision(
                    allowed=result.get("allow", False),
                    violations=[
                        {"code": v.get("code"), "message": v.get("message")} 
                        for v in result.get("violations", [])
                    ],
                    policy_version=result.get("policy_version", "unknown"),
                    policy_hash=get_policy_metadata()["hash"]
                )
        except httpx.RequestError as e:
            logger.error("OPA_UNAVAILABLE", error=str(e))
            raise PolicyUnavailable("Policy engine is unavailable") from e
        except httpx.HTTPStatusError as e:
            logger.error("OPA_HTTP_ERROR", status=e.response.status_code)
            raise PolicyUnavailable(f"Policy engine returned error: {e.response.status_code}") from e
        except Exception as e:
            logger.error("OPA_EVALUATION_ERROR", error=str(e))
            raise PolicyUnavailable(f"Error evaluating policy: {e}") from e
