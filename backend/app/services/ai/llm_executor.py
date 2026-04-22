"""
LLM executor service for AdTicks.
Runs prompts against OpenAI, Anthropic Claude, and Gemini (mocked).
Handles async batch execution with rate limiting.
"""

import logging
import asyncio
import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = logging.getLogger(__name__)

OPENAI_MODEL = "gpt-4o"
CLAUDE_MODEL = "claude-3-5-sonnet-20241022"
GEMINI_MODEL = "gemini-1.5-pro"

# Rate limiting: requests per minute
OPENAI_RPM = 50
CLAUDE_RPM = 40
GEMINI_RPM = 30


class RateLimiter:
    """Token bucket rate limiter for API calls."""

    def __init__(self, rpm: int):
        self.rpm = rpm
        self._interval = 60.0 / rpm  # seconds between requests
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
_claude_limiter = RateLimiter(CLAUDE_RPM)
_gemini_limiter = RateLimiter(GEMINI_RPM)


async def query_openai(
    prompt_text: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 1500,
) -> str:
    """
    Query OpenAI GPT-4o with a prompt.

    Args:
        prompt_text: The user prompt to send
        system_prompt: Optional system prompt override
        temperature: Sampling temperature 0-1
        max_tokens: Maximum response tokens

    Returns:
        Response text string
    """
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
        logger.debug(f"OpenAI response: {len(text)} chars for prompt snippet: {prompt_text[:60]}")
        return text
    except Exception as e:
        logger.error(f"OpenAI query failed: {e}")
        raise


async def query_claude(
    prompt_text: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 1500,
) -> str:
    """
    Query Anthropic Claude with a prompt.

    Args:
        prompt_text: The user prompt to send
        system_prompt: Optional system prompt override
        temperature: Sampling temperature 0-1
        max_tokens: Maximum response tokens

    Returns:
        Response text string
    """
    if not ANTHROPIC_AVAILABLE:
        raise RuntimeError("Anthropic package not installed")

    await _claude_limiter.acquire()
    client = anthropic.AsyncAnthropic()
    sys_msg = system_prompt or "You are a helpful AI assistant. Answer questions concisely and accurately."

    try:
        message = await client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=max_tokens,
            system=sys_msg,
            messages=[{"role": "user", "content": prompt_text}],
        )
        text = message.content[0].text if message.content else ""
        logger.debug(f"Claude response: {len(text)} chars for prompt snippet: {prompt_text[:60]}")
        return text
    except Exception as e:
        logger.error(f"Claude query failed: {e}")
        raise


async def query_gemini(
    prompt_text: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 1500,
) -> str:
    """
    Query Google Gemini (mocked — placeholder for real Gemini integration).

    Args:
        prompt_text: The user prompt to send
        system_prompt: Optional system prompt override
        temperature: Sampling temperature 0-1
        max_tokens: Maximum response tokens

    Returns:
        Mocked response text string
    """
    await _gemini_limiter.acquire()
    logger.info(f"Gemini mock query for: {prompt_text[:60]}")

    # Realistic mock response
    await asyncio.sleep(0.5)  # Simulate API latency
    mock_responses = [
        f"Based on my knowledge, {prompt_text.lower().replace('?', '')} is an important topic. Here's what I know: this relates to modern software solutions that help businesses achieve their goals. Multiple providers offer solutions in this space, each with distinct advantages.",
        f"Great question about {prompt_text[:50]}. In my analysis, there are several key considerations: first, the market has multiple strong players. Second, the choice depends heavily on your specific use case and budget. Third, customer support and integration capabilities are crucial differentiators.",
        f"Regarding {prompt_text[:40]}: this is a competitive space with several notable options. The best choice depends on your team size, technical requirements, and growth stage. I'd recommend evaluating based on features, pricing transparency, and customer reviews.",
    ]
    import random
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
    """Execute a single prompt against one model with error handling."""
    async with semaphore:
        prompt_id = prompt.get("id", str(uuid.uuid4()))
        prompt_text = prompt.get("text", "")

        try:
            if model == "openai":
                text = await query_openai(prompt_text)
            elif model == "claude":
                text = await query_claude(prompt_text)
            elif model == "gemini":
                text = await query_gemini(prompt_text)
            else:
                raise ValueError(f"Unknown model: {model}")

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
    """
    Run a batch of prompts against multiple LLM models with rate limiting.

    Args:
        prompts: List of prompt dicts with 'id' and 'text' fields
        models: List of model names to query. Defaults to ['openai', 'claude']
        concurrency: Max concurrent requests per model

    Returns:
        List of response dicts with model outputs
    """
    if models is None:
        models = ["openai", "claude"]

    logger.info(f"Running batch: {len(prompts)} prompts x {len(models)} models = {len(prompts)*len(models)} total requests")
    semaphore = asyncio.Semaphore(concurrency)

    all_tasks = []
    for model in models:
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
    """
    Persist a response dict as JSON to the storage path.

    Args:
        response: Response dict from run_prompt_batch
        base_path: Base directory for storage

    Returns:
        Storage path string where file was written
    """
    import os
    import aiofiles  # type: ignore

    model = response.get("model", "unknown")
    prompt_id = response.get("prompt_id", str(uuid.uuid4()))
    dir_path = os.path.join(base_path, model)
    os.makedirs(dir_path, exist_ok=True)

    file_path = os.path.join(dir_path, f"{prompt_id}.json")
    try:
        async with aiofiles.open(file_path, "w") as f:
            await f.write(json.dumps(response, indent=2))
        logger.debug(f"Stored response to {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Failed to store response: {e}")
        return response.get("storage_path", file_path)
