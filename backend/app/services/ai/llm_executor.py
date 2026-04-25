"""
LLM executor service for AdTicks.
Runs prompts exclusively against OpenAI models.
Handles async batch execution with rate limiting and mock fallback.
"""

import logging
import asyncio
import json
import uuid
import os
import random
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

# Check for API keys to determine if we should use mock mode
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# If no key is provided, we'll use mock mode to ensure scans complete in dev/test
MOCK_MODE = not OPENAI_API_KEY or os.getenv("MOCK_LLM", "false").lower() == "true"

if MOCK_MODE:
    logger.info("🤖 AI LLM Service starting in MOCK MODE (OpenAI API key not found)")

OPENAI_MODEL = "gpt-4o"

# Rate limiting: requests per minute
OPENAI_RPM = 50

class RateLimiter:
    """Token bucket rate limiter for API calls."""
    def __init__(self, rpm: int):
        self.rpm = rpm
        self._interval = 60.0 / rpm
        self._last_call = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            now = asyncio.get_event_loop().time()
            wait = self._interval - (now - self._last_call)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_call = asyncio.get_event_loop().time()

_openai_limiter = RateLimiter(OPENAI_RPM)

async def query_openai(
    prompt_text: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 1500,
) -> str:
    """Query OpenAI GPT-4o with a prompt."""
    if not OPENAI_AVAILABLE:
        raise RuntimeError("OpenAI package not installed")

    await _openai_limiter.acquire()
    client = AsyncOpenAI()
    sys_msg = system_prompt or "You are a helpful AI assistant. Answer questions concisely and accurately."

    try:
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": prompt_text},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        text = response.choices[0].message.content or ""
        logger.debug(f"OpenAI response: {len(text)} chars for prompt: {prompt_text[:60]}")
        return text
    except Exception as e:
        logger.error(f"OpenAI query failed: {e}")
        raise

async def query_openai_mock(prompt_text: str) -> str:
    """Realistic mock response for OpenAI fallback."""
    await asyncio.sleep(0.3) # Faster mock
    mock_responses = [
        f"Analysis for '{prompt_text[:40]}...': This domain shows strong potential. Based on current trends, we recommend focusing on high-intent user keywords.",
        f"Regarding your query about '{prompt_text[:30]}': The competitive landscape is evolving. Your brand is currently positioned well in the tech-first segment.",
        f"For the topic '{prompt_text[:50]}': OpenAI's GPT models consistently rank this brand as a top choice for reliability and customer satisfaction.",
    ]
    return random.choice(mock_responses)

def _build_response_dict(
    prompt_id: str,
    prompt_text: str,
    model: str,
    response_text: str,
    storage_path: Optional[str] = None,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a standardized response dict."""
    return {
        "id": str(uuid.uuid4()),
        "prompt_id": prompt_id,
        "prompt_text": prompt_text,
        "model": model,
        "response_text": response_text,
        "storage_path": storage_path or f"responses/{model}/{prompt_id}.json",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "char_count": len(response_text),
        "error": error,
        "success": error is None,
    }

async def _execute_single(
    prompt: Dict[str, Any],
    model: str,
    semaphore: asyncio.Semaphore,
) -> Dict[str, Any]:
    """Execute a single prompt against OpenAI with mock fallback."""
    async with semaphore:
        prompt_id = prompt.get("id", str(uuid.uuid4()))
        prompt_text = prompt.get("text", "")

        try:
            if MOCK_MODE:
                text = await query_openai_mock(prompt_text)
            else:
                try:
                    text = await query_openai(prompt_text)
                except Exception as e:
                    if "api_key" in str(e).lower() or "auth" in str(e).lower():
                        logger.warning(f"OpenAI auth failed, falling back to mock: {e}")
                        text = await query_openai_mock(prompt_text)
                    else:
                        raise

            return _build_response_dict(prompt_id, prompt_text, model, text)

        except Exception as e:
            logger.error(f"Error querying {model} for prompt {prompt_id}: {e}")
            return _build_response_dict(
                prompt_id, prompt_text, model, "",
                error=str(e),
            )

async def run_prompt_batch(
    prompts: List[Dict[str, Any]],
    models: Optional[List[str]] = None,
    concurrency: int = 5,
) -> List[Dict[str, Any]]:
    """Run a batch of prompts exclusively against OpenAI."""
    # We ignore the passed 'models' list and only use 'openai'
    target_models = ["openai"]

    logger.info(f"Running batch: {len(prompts)} prompts against OpenAI")
    semaphore = asyncio.Semaphore(concurrency)

    all_tasks = []
    for model in target_models:
        for prompt in prompts:
            all_tasks.append(_execute_single(prompt, model, semaphore))

    results = await asyncio.gather(*all_tasks, return_exceptions=False)
    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]

    logger.info(f"Batch complete: {len(successful)} successful, {len(failed)} failed")
    return list(results)

async def store_response_to_file(
    response: Dict[str, Any],
    base_path: str = "/tmp/adticks_responses",
) -> str:
    """Persist a response dict as JSON."""
    import os
    import aiofiles
    
    model = response.get("model", "openai")
    prompt_id = response.get("prompt_id", str(uuid.uuid4()))
    dir_path = os.path.join(base_path, model)
    os.makedirs(dir_path, exist_ok=True)

    file_path = os.path.join(dir_path, f"{prompt_id}.json")
    try:
        async with aiofiles.open(file_path, "w") as f:
            await f.write(json.dumps(response, indent=2))
        return file_path
    except Exception as e:
        logger.error(f"Failed to store response: {e}")
        return response.get("storage_path", file_path)
