"""
LLM executor service for AdTicks.
Primary: Ollama (Mistral 7B) - Cost-free, fast, privacy-focused
Fallback: OpenAI (gpt-4o) - Reliable backup if Ollama fails
Handles async batch execution with rate limiting and graceful fallback.
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

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

logger = logging.getLogger(__name__)

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = "mistral"  # Mistral 7B - excellent quality/speed balance

# Determine if we should use mock mode (when no real providers available)
MOCK_MODE = os.getenv("MOCK_LLM", "false").lower() == "true"

OPENAI_MODEL = "gpt-4o"
OPENAI_RPM = 50  # Rate limiting: requests per minute

logger.info(f"🤖 LLM Service initializing...")
logger.info(f"   Primary: Ollama ({OLLAMA_MODEL}) at {OLLAMA_HOST}")
logger.info(f"   Fallback: OpenAI ({OPENAI_MODEL}) - {'Available' if OPENAI_API_KEY else 'Not configured'}")
logger.info(f"   Mock Mode: {MOCK_MODE}")


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


async def pull_ollama_model(model_name: str):
    """Pull a model from Ollama library."""
    logger.info(f"🚚 Pulling Ollama model: {model_name}... This may take a few minutes.")
    try:
        async with httpx.AsyncClient(timeout=600.0) as client:
            response = await client.post(
                f"{OLLAMA_HOST}/api/pull",
                json={"name": model_name, "stream": False},
            )
            if response.status_code == 200:
                logger.info(f"✅ Successfully pulled Ollama model: {model_name}")
            else:
                logger.error(f"❌ Failed to pull Ollama model: {response.text}")
    except Exception as e:
        logger.error(f"❌ Error pulling Ollama model: {e}")


async def query_ollama(
    prompt_text: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 1500,
) -> str:
    """Query Ollama with Mistral 7B model."""
    if not HTTPX_AVAILABLE:
        raise RuntimeError("httpx package not installed")

    sys_msg = system_prompt or "You are a helpful AI assistant. Answer questions concisely and accurately."
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OLLAMA_HOST}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [
                        {"role": "system", "content": sys_msg},
                        {"role": "user", "content": prompt_text},
                    ],
                    "temperature": temperature,
                    "stream": False,
                },
            )
            
            if response.status_code == 404:
                error_data = response.json()
                if "not found" in error_data.get("error", "").lower():
                    logger.warning(f"⚠️  Ollama model '{OLLAMA_MODEL}' not found. Attempting automatic pull...")
                    await pull_ollama_model(OLLAMA_MODEL)
                    # Retry once after pulling
                    return await query_ollama(prompt_text, system_prompt, temperature, max_tokens)

            if response.status_code != 200:
                raise Exception(f"Ollama returned {response.status_code}: {response.text}")
            
            data = response.json()
            text = data.get("message", {}).get("content", "")
            logger.debug(f"Ollama response: {len(text)} chars for prompt: {prompt_text[:60]}")
            return text
            
    except Exception as e:
        logger.warning(f"Ollama query failed: {e}")
        raise


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


async def query_mock(prompt_text: str) -> str:
    """Realistic mock response for fallback."""
    await asyncio.sleep(0.3)
    mock_responses = [
        f"Analysis for '{prompt_text[:40]}...': This domain shows strong potential. Based on current trends, we recommend focusing on high-intent user keywords.",
        f"Regarding your query about '{prompt_text[:30]}': The competitive landscape is evolving. Your brand is currently positioned well in the tech-first segment.",
        f"For the topic '{prompt_text[:50]}': Our analysis shows consistent performance across key metrics with room for optimization in the technical SEO area.",
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
    semaphore: asyncio.Semaphore,
) -> Dict[str, Any]:
    """
    Execute a single prompt with intelligent fallback:
    1. Try Ollama first (primary, cost-free)
    2. If Ollama fails, try OpenAI (reliable backup)
    3. If both fail, use mock (development fallback)
    """
    async with semaphore:
        prompt_id = prompt.get("id", str(uuid.uuid4()))
        prompt_text = prompt.get("text", "")
        model_used = "unknown"
        text = ""

        try:
            # 1. Try Ollama first (primary)
            try:
                text = await query_ollama(prompt_text)
                model_used = "ollama"
                logger.info(f"✅ Ollama succeeded for prompt {prompt_id}")
                return _build_response_dict(prompt_id, prompt_text, model_used, text)
            except Exception as e:
                logger.warning(f"⚠️  Ollama failed, trying OpenAI fallback: {str(e)[:100]}")

            # 2. Try OpenAI fallback (reliable backup)
            if OPENAI_API_KEY and OPENAI_AVAILABLE:
                try:
                    text = await query_openai(prompt_text)
                    model_used = "openai"
                    logger.info(f"✅ OpenAI fallback succeeded for prompt {prompt_id}")
                    return _build_response_dict(prompt_id, prompt_text, model_used, text)
                except Exception as e:
                    logger.warning(f"⚠️  OpenAI also failed: {str(e)[:100]}")

            # 3. Use mock (development/testing)
            if MOCK_MODE:
                text = await query_mock(prompt_text)
                model_used = "mock"
                logger.info(f"ℹ️  Using mock response for prompt {prompt_id}")
                return _build_response_dict(prompt_id, prompt_text, model_used, text)

            # If we get here, nothing worked and mock is disabled
            raise RuntimeError("All LLM providers failed and mock mode is disabled")

        except Exception as e:
            logger.error(f"❌ Error executing prompt {prompt_id}: {e}")
            return _build_response_dict(
                prompt_id, prompt_text, model_used or "error", "",
                error=str(e),
            )


async def run_prompt_batch(
    prompts: List[Dict[str, Any]],
    models: Optional[List[str]] = None,
    concurrency: int = 5,
) -> List[Dict[str, Any]]:
    """
    Run a batch of prompts with intelligent fallback.
    Primary: Ollama (cost-free, fast)
    Fallback: OpenAI (reliable)
    Mock: Development mode
    """
    logger.info(f"🚀 Running batch: {len(prompts)} prompts (Primary: Ollama → Fallback: OpenAI)")
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
