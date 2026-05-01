"""
LLM executor service for AdTicks.
Primary: OpenAI (gpt-4o) - Reliable, high-quality analysis
No fallback: Skips runs if OpenAI is not configured or fails.
Handles async batch execution with rate limiting.
"""

import logging
import asyncio
import json
import uuid
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o"
OPENAI_RPM = 50  # Rate limiting: requests per minute

logger.info(f"🤖 LLM Service initializing...")
logger.info(f"   Primary: OpenAI ({OPENAI_MODEL}) - {'Available' if (OPENAI_API_KEY and OPENAI_AVAILABLE) else 'Not configured'}")


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

    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not configured")

    await _openai_limiter.acquire()
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
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
    semaphore: asyncio.Semaphore,
) -> Dict[str, Any]:
    """
    Execute a single prompt using OpenAI.
    No fallback to mock data.
    """
    async with semaphore:
        prompt_id = prompt.get("id", str(uuid.uuid4()))
        prompt_text = prompt.get("text", "")
        model_used = "openai"
        
        if not OPENAI_API_KEY or not OPENAI_AVAILABLE:
            logger.warning(f"⏩ Skipping prompt {prompt_id}: OpenAI not configured")
            return _build_response_dict(
                prompt_id, prompt_text, "skipped", "",
                error="OpenAI provider not configured"
            )

        try:
            text = await query_openai(prompt_text)
            logger.info(f"✅ OpenAI succeeded for prompt {prompt_id}")
            return _build_response_dict(prompt_id, prompt_text, model_used, text)
        except Exception as e:
            logger.error(f"❌ Error executing prompt {prompt_id}: {e}")
            return _build_response_dict(
                prompt_id, prompt_text, model_used, "",
                error=str(e),
            )


async def run_prompt_batch(
    prompts: List[Dict[str, Any]],
    models: Optional[List[str]] = None,
    concurrency: int = 5,
) -> List[Dict[str, Any]]:
    """
    Run a batch of prompts using OpenAI.
    Skips runs if OpenAI is not available.
    """
    if not OPENAI_API_KEY or not OPENAI_AVAILABLE:
        logger.error("🛑 Cannot run batch: OpenAI not configured. Skipping all prompts.")
        return [
            _build_response_dict(p.get("id", str(uuid.uuid4())), p.get("text", ""), "skipped", "", error="OpenAI not configured")
            for p in prompts
        ]

    logger.info(f"🚀 Running batch: {len(prompts)} prompts (Primary: OpenAI)")
    semaphore = asyncio.Semaphore(concurrency)

    tasks = [_execute_single(prompt, semaphore) for prompt in prompts]
    results = await asyncio.gather(*tasks, return_exceptions=False)

    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]
    
    # Count by model
    model_counts = {}
    for r in successful:
        model = r.get("model", "unknown")
        model_counts[model] = model_counts.get(model, 0) + 1

    model_summary = ", ".join([f"{m}:{c}" for m, c in model_counts.items()])
    logger.info(f"✅ Batch complete: {len(successful)}/{len(prompts)} successful [{model_summary}], {len(failed)} failed")

    return list(results)


async def store_response_to_file(
    response: Dict[str, Any],
    base_path: str = "/tmp/adticks_responses",
) -> str:
    """Persist a response dict as JSON."""
    import aiofiles
    
    model = response.get("model", "unknown")
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
