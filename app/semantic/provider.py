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
            async with httpx.AsyncClient(timeout=30.0) as client:
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

import asyncio
from google import genai
from google.genai import types
from google.genai.errors import APIError
from pydantic import ValidationError
from app.domain.models import SemanticAssessment

class GeminiLLMProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-3.6-flash"):
        self.api_key = api_key
        self.model = model
        # Initialize sync and async clients
        self.client = genai.Client(api_key=api_key)

    async def generate_json(self, system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> dict:
        try:
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                                response_schema={
                    "type": "OBJECT",
                    "properties": {
                        "status": {"type": "STRING", "enum": ["PASS", "REVIEW", "FAIL"]},
                        "confidence": {"type": "NUMBER"},
                        "checks": {"type": "OBJECT"},
                        "violations": {
                            "type": "ARRAY",
                            "items": {
                                "type": "OBJECT",
                                "properties": {
                                    "type": {"type": "STRING"},
                                    "severity": {"type": "STRING", "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]},
                                    "evidence": {"type": "STRING"}
                                },
                                "required": ["type", "severity", "evidence"]
                            }
                        },
                        "reasoning": {"type": "STRING"}
                    },
                    "required": ["status", "confidence", "checks", "violations", "reasoning"]
                },
                temperature=0.0,
                max_output_tokens=max_tokens
            )

            # Using asyncio.wait_for to ensure a bounded timeout (e.g., 10 seconds)
            async def _call():
                return await self.client.aio.models.generate_content(
                    model=self.model,
                    contents=user_prompt,
                    config=config
                )

            start_time = asyncio.get_event_loop().time()
            response = await asyncio.wait_for(_call(), timeout=30.0)
            latency = asyncio.get_event_loop().time() - start_time

            logger.info("GEMINI_API_CALL", model=self.model, latency=f"{latency:.3f}s", status="SUCCESS")

            if not response.text:
                raise LLMProviderError("Empty response from Gemini")

            if response.parsed:
                return response.parsed if isinstance(response.parsed, dict) else response.parsed.model_dump()
            else:
                return json.loads(response.text)

        except asyncio.TimeoutError as e:
            logger.error("LLM_TIMEOUT", error="Gemini API request timed out")
            raise LLMProviderError("LLM request timed out") from e
        except APIError as e:
            logger.error("GEMINI_API_ERROR", error=str(e))
            raise LLMProviderError(f"Gemini API error: {e}") from e
        except json.JSONDecodeError as e:
            logger.error("LLM_INVALID_JSON", error=str(e))
            raise LLMProviderError("LLM returned invalid JSON") from e
        except Exception as e:
            logger.error("LLM_PROVIDER_ERROR", error=str(e))
            raise LLMProviderError(f"LLM request failed: {e}") from e

def get_provider(provider_type: str = "mock", api_key: str = "", model: str = "gemini-3.6-flash"):
    if provider_type == "anthropic":
        return AnthropicLLMProvider(api_key=api_key)
    elif provider_type == "gemini":
        return GeminiLLMProvider(api_key=api_key, model=model)
    return MockLLMProvider()
