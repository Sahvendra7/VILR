import re
with open("app/semantic/provider.py", "r") as f:
    text = f.read()

new_provider = """
import asyncio
from google import genai
from google.genai import types
from google.genai.errors import APIError
from pydantic import ValidationError
from app.domain.models import SemanticAssessment

class GeminiLLMProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model = model
        # Initialize sync and async clients
        self.client = genai.Client(api_key=api_key)
        
    async def generate_json(self, system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> dict:
        try:
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=SemanticAssessment,
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
            response = await asyncio.wait_for(_call(), timeout=10.0)
            latency = asyncio.get_event_loop().time() - start_time
            
            logger.info("GEMINI_API_CALL", model=self.model, latency=f"{latency:.3f}s", status="SUCCESS")
            
            if not response.text:
                raise LLMProviderError("Empty response from Gemini")
                
            if response.parsed:
                return response.parsed.model_dump()
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

def get_provider(provider_type: str = "mock", api_key: str = "", model: str = "gemini-2.5-flash"):
    if provider_type == "anthropic":
        return AnthropicLLMProvider(api_key=api_key)
    elif provider_type == "gemini":
        return GeminiLLMProvider(api_key=api_key, model=model)
    return MockLLMProvider()
"""

# replace get_provider at the end
text = re.sub(r'def get_provider.*?$', new_provider.strip(), text, flags=re.DOTALL)
with open("app/semantic/provider.py", "w") as f:
    f.write(text)
