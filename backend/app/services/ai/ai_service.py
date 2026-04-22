"""
Main AI service coordinator for AdTicks.
Orchestrates prompt generation, LLM execution, mention extraction, and scoring.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from .prompt_generator import generate_prompts
from .llm_executor import run_prompt_batch
from .mention_extractor import extract_mentions, aggregate_mention_stats
from .scorer import compute_visibility_score

logger = logging.getLogger(__name__)


async def run_ai_visibility_scan(
    project_id: str,
    brand_name: str,
    domain: str,
    industry: str,
    competitors: Optional[List[str]] = None,
    models: Optional[List[str]] = None,
    prompt_limit: Optional[int] = None,
    scan_count: int = 0,
) -> Dict[str, Any]:
    """
    Run a full AI visibility scan: generate prompts, query LLMs, extract mentions, score.

    Args:
        project_id: Project identifier
        brand_name: Target brand name
        domain: Brand domain
        industry: Industry category
        competitors: List of competitor brand names
        models: LLM models to query (defaults to ['openai', 'claude'])
        prompt_limit: Max prompts to run (for free tier limiting)
        scan_count: Current scan count for usage tracking

    Returns:
        Full scan results dict with prompts, responses, mentions, and scores
    """
    logger.info(f"[{project_id}] Starting AI visibility scan: brand={brand_name}")
    start_time = datetime.now(timezone.utc)

    competitors = competitors or []
    models = models or ["openai", "claude"]

    # Step 1: Generate prompts
    logger.info(f"[{project_id}] Step 1: Generating prompts")
    all_prompts = await generate_prompts(brand_name, domain, industry, competitors)

    # Apply limit for free tier
    if prompt_limit and len(all_prompts) > prompt_limit:
        logger.info(f"Limiting prompts to {prompt_limit} (free tier)")
        all_prompts = all_prompts[:prompt_limit]

    # Step 2: Execute prompts against LLMs
    logger.info(f"[{project_id}] Step 2: Running {len(all_prompts)} prompts against {models}")
    responses = await run_prompt_batch(all_prompts, models=models, concurrency=5)

    # Group responses by prompt_id and model
    response_map: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for resp in responses:
        pid = resp.get("prompt_id", "")
        model = resp.get("model", "unknown")
        if pid not in response_map:
            response_map[pid] = {}
        response_map[pid][model] = resp

    # Step 3: Extract mentions from all responses
    logger.info(f"[{project_id}] Step 3: Extracting brand mentions")
    prompt_results: List[Dict[str, Any]] = []
    all_mentions: List[Dict[str, Any]] = []

    for prompt in all_prompts:
        pid = prompt["id"]
        prompt_model_responses = response_map.get(pid, {})
        prompt_mentions: List[Dict[str, Any]] = []
        prompt_all_mentions: List[Dict[str, Any]] = []

        for model, resp in prompt_model_responses.items():
            response_text = resp.get("response_text", "")
            if not response_text or resp.get("error"):
                continue

            # Extract target brand mentions
            target_mentions = extract_mentions(
                response_text, brand_name, competitors, response_id=resp.get("id")
            )
            prompt_mentions.extend([m for m in target_mentions if m.get("is_target_brand")])
            prompt_all_mentions.extend(target_mentions)  # Includes competitor mentions

        all_mentions.extend(prompt_mentions)

        prompt_results.append({
            "prompt": prompt,
            "responses": list(prompt_model_responses.values()),
            "mentions": prompt_mentions,
            "all_mentions": prompt_all_mentions,
            "mentioned": len(prompt_mentions) > 0,
        })

    # Step 4: Compute scores
    logger.info(f"[{project_id}] Step 4: Computing visibility scores")
    score = compute_visibility_score(
        project_id=project_id,
        prompt_results=prompt_results,
        target_brand=brand_name,
        industry=industry,
        scan_count=scan_count,
    )

    # Step 5: Aggregate mention stats
    mention_stats = aggregate_mention_stats(all_mentions, brand_name)

    end_time = datetime.now(timezone.utc)
    duration = (end_time - start_time).total_seconds()

    result = {
        "project_id": project_id,
        "brand_name": brand_name,
        "scan_started": start_time.isoformat(),
        "scan_completed": end_time.isoformat(),
        "duration_seconds": round(duration, 2),
        "models_queried": models,
        "prompts": all_prompts,
        "prompt_count": len(all_prompts),
        "responses": responses,
        "response_count": len(responses),
        "mentions": all_mentions,
        "mention_stats": mention_stats,
        "prompt_results": prompt_results,
        "score": score,
        "visibility_pct": round(score["visibility_score"] * 100, 1),
    }

    logger.info(
        f"[{project_id}] AI scan complete in {duration:.1f}s: "
        f"visibility={score['visibility_score']:.1%} "
        f"sov={score['sov_score']:.1%}"
    )
    return result
