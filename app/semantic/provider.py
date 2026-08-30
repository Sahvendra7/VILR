import httpx
import structlog
import json
from typing import Dict, Any, Union
from app.domain.interfaces import LLMProvider
from app.domain.errors import VILRError

logger = structlog.get_logger(__name__)

class LLMProviderError(VILRError):
    pass

class MockLLMProvider(LLMProvider):
    def __init__(self, responses: Dict[str, Any] = None):
        self.responses = responses or {}
        
    async def generate_json(self, system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> dict:
        for key, resp in self.responses.items():
            if key in user_prompt:
                if isinstance(resp, Exception):
                    raise resp
                if isinstance(resp, str):
                    try:
                        return json.loads(resp)
                    except json.JSONDecodeError:
                        raise LLMProviderError("LLM returned invalid JSON")
                return resp
                
        return {
            "status": "PASS",
            "confidence": 0.95,
            "checks": {},
            "violations": [],
            "reasoning": "Mock passed"
        }

class AnthropicLLMProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        self.api_key = api_key
        self.model = model
        self.url = "https://api.anthropic.com/v1/messages"
        
    async def generate_json(self, system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> dict:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}]
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self.url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                content = data["content"][0]["text"]
                
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                    
                return json.loads(content)
        except httpx.TimeoutException as e:
            logger.error("LLM_TIMEOUT", error=str(e))
            raise LLMProviderError("LLM request timed out") from e
        except json.JSONDecodeError as e:
            logger.error("LLM_INVALID_JSON", error=str(e), raw_content=content)
            raise LLMProviderError("LLM returned invalid JSON") from e
        except Exception as e:
            logger.error("LLM_PROVIDER_ERROR", error=str(e))
            raise LLMProviderError(f"LLM request failed: {e}") from e
