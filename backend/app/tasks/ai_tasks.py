"""AI visibility Celery tasks — full implementation."""
import asyncio
import logging
import uuid
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.core.storage import StorageService
from app.models.project import Project
from app.models.competitor import Competitor
from app.models.prompt import Prompt, Response, Mention
from app.models.score import Score
from app.services.ai.ai_service import run_ai_visibility_scan
from app.services.ai.prompt_generator import generate_prompts
from app.services.ai.mention_extractor import extract_mentions

logger = logging.getLogger(__name__)
storage = StorageService()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _load_project(session, project_id: str):
    from sqlalchemy import select
    result = await session.execute(select(Project).where(Project.id == project_id))
    return result.scalar_one_or_none()


async def _load_competitors(session, project_id: str):
    result = await session.execute(
        select(Competitor).where(Competitor.project_id == project_id)
    )
    return result.scalars().all()


# ---------------------------------------------------------------------------
# generate_prompts_task
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def generate_prompts_task(
    self,
    project_id: str,
    brand_name: str,
    domain: str,
    industry: str,
    competitors: list | None = None,
) -> dict:
    """Generate AI prompts for a project and persist to DB + Spaces."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            _generate_prompts_impl(project_id, brand_name, domain, industry, competitors or [])
        )
        loop.close()
        return result
    except Exception as exc:
        logger.exception("generate_prompts_task failed for project %s: %s", project_id, exc)
        raise self.retry(exc=exc)


async def _generate_prompts_impl(
    project_id: str,
    brand_name: str,
    domain: str,
    industry: str,
    competitors: list,
) -> dict:
    logger.info(
        "Generating prompts for project=%s brand=%s industry=%s",
        project_id, brand_name, industry,
    )

    # Load project info if available to override defaults
    async with AsyncSessionLocal() as session:
        project = await _load_project(session, project_id)
        if project:
            brand_name = project.brand_name or brand_name
            domain = project.domain or domain
            industry = project.industry or industry
        if not competitors:
            comp_objs = await _load_competitors(session, project_id)
            competitors = [c.domain for c in comp_objs]

    prompts_raw = await generate_prompts(brand_name, domain, industry, competitors)
    logger.info("Service returned %d prompts", len(prompts_raw))

    # Bulk insert Prompt rows
    async with AsyncSessionLocal() as session:
        for p in prompts_raw:
            prompt_row = Prompt(
                id=uuid.UUID(p["id"]) if p.get("id") else uuid.uuid4(),
                project_id=UUID(project_id),
                text=p["text"],
                category=p.get("category"),
                created_at=datetime.now(timezone.utc),
            )
            session.add(prompt_row)
        await session.commit()
        logger.info("Inserted %d Prompt rows for project %s", len(prompts_raw), project_id)

    # Store to Spaces
    payload = {
        "project_id": project_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "prompt_count": len(prompts_raw),
        "prompts": prompts_raw,
    }
    try:
        storage.upload_json(StorageService.ai_path(project_id, "prompts.json"), payload)
    except Exception as exc:
        logger.warning("Spaces upload failed (non-fatal): %s", exc)

    return {
        "project_id": project_id,
        "prompts_generated": len(prompts_raw),
        "status": "completed",
    }


# ---------------------------------------------------------------------------
# run_llm_scan_task
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, max_retries=3, default_retry_delay=120)
def run_llm_scan_task(self, project_id: str, prompt_limit: int = 100) -> dict:
    """Run AI visibility scan: execute prompts against LLMs, store results, score."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            _run_llm_scan_impl(project_id, prompt_limit)
        )
        loop.close()
        return result
    except Exception as exc:
        logger.exception("run_llm_scan_task failed for project %s: %s", project_id, exc)
        raise self.retry(exc=exc)


async def _run_llm_scan_impl(project_id: str, prompt_limit: int) -> dict:
    logger.info("Running LLM scan for project=%s limit=%d", project_id, prompt_limit)

    async with AsyncSessionLocal() as session:
        project = await _load_project(session, project_id)
        if not project:
            return {"project_id": project_id, "status": "project_not_found"}
        competitors = await _load_competitors(session, project_id)
        competitor_domains = [c.domain for c in competitors]

    # Run full AI visibility scan via service
    scan_result = await run_ai_visibility_scan(
        project_id=project_id,
        brand_name=project.brand_name,
        domain=project.domain,
        industry=project.industry or "Technology",
        competitors=competitor_domains,
        prompt_limit=prompt_limit,
    )

    prompt_results = scan_result.get("prompt_results", [])
    all_responses = scan_result.get("responses", [])
    score_data = scan_result.get("score", {})

    # Persist responses and mentions
    async with AsyncSessionLocal() as session:
        for pr in prompt_results:
            prompt_info = pr.get("prompt", {})
            prompt_id_str = prompt_info.get("id")
            if not prompt_id_str:
                continue

            # Verify prompt exists in DB (it should from generate_prompts_task)
            # If not, we skip silently
            try:
                prompt_uuid = uuid.UUID(prompt_id_str)
            except (ValueError, AttributeError):
                prompt_uuid = uuid.uuid4()

            for resp_data in pr.get("responses", []):
                resp_id = uuid.uuid4()
                storage_path = StorageService.ai_path(
                    project_id, f"responses/{str(prompt_uuid)}.json"
                )
                # Store raw response to Spaces
                try:
                    storage.upload_json(storage_path, {
                        "prompt_id": str(prompt_uuid),
                        "response": resp_data,
                        "scan_id": scan_result.get("project_id"),
                    })
                except Exception as exc:
                    logger.warning("Response Spaces upload failed: %s", exc)

                resp_row = Response(
                    id=resp_id,
                    prompt_id=prompt_uuid,
                    storage_path=storage_path,
                    model=resp_data.get("model"),
                    timestamp=datetime.now(timezone.utc),
                )
                session.add(resp_row)
                await session.flush()

                # Persist mentions for this response
                for mention_data in pr.get("all_mentions", []):
                    if mention_data.get("response_id") and mention_data["response_id"] != resp_data.get("id"):
                        continue
                    mention_row = Mention(
                        id=uuid.uuid4(),
                        response_id=resp_id,
                        brand=mention_data.get("brand", ""),
                        position=_position_str_to_int(mention_data.get("position")),
                        confidence=mention_data.get("confidence"),
                    )
                    session.add(mention_row)

        # Persist Score row
        score_row = Score(
            id=uuid.uuid4(),
            project_id=UUID(project_id),
            visibility_score=score_data.get("visibility_score"),
            impact_score=score_data.get("impact_score"),
            sov_score=score_data.get("sov_score"),
            timestamp=datetime.now(timezone.utc),
        )
        session.add(score_row)
        await session.commit()
        logger.info("Persisted scan results for project %s", project_id)

    return {
        "project_id": project_id,
        "prompts_run": scan_result.get("prompt_count", 0),
        "responses_stored": len(all_responses),
        "mentions_found": scan_result.get("mention_stats", {}).get("total_mentions", 0),
        "visibility_score": score_data.get("visibility_score", 0.0),
        "sov_score": score_data.get("sov_score", 0.0),
        "impact_score": score_data.get("impact_score", 0.0),
        "status": "completed",
    }


def _position_str_to_int(position) -> int | None:
    """Convert 'first'/'middle'/'last' or numeric to an integer rank proxy."""
    mapping = {"first": 1, "middle": 2, "last": 3}
    if isinstance(position, str):
        return mapping.get(position.lower())
    if isinstance(position, int):
        return position
    return None


# ---------------------------------------------------------------------------
# extract_mentions_task
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def extract_mentions_task(
    self,
    response_id: str,
    response_text: str,
    target_brand: str,
    competitor_brands: list,
) -> dict:
    """Extract brand mentions from a single LLM response and persist Mention rows."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            _extract_mentions_impl(response_id, response_text, target_brand, competitor_brands)
        )
        loop.close()
        return result
    except Exception as exc:
        logger.exception("extract_mentions_task failed for response %s: %s", response_id, exc)
        raise self.retry(exc=exc)


async def _extract_mentions_impl(
    response_id: str,
    response_text: str,
    target_brand: str,
    competitor_brands: list,
) -> dict:
    logger.info("Extracting mentions from response=%s", response_id)

    mentions_raw = extract_mentions(
        response_text=response_text,
        target_brand=target_brand,
        competitor_brands=competitor_brands,
        response_id=response_id,
    )

    async with AsyncSessionLocal() as session:
        for m in mentions_raw:
            mention_row = Mention(
                id=uuid.uuid4(),
                response_id=uuid.UUID(response_id) if response_id else uuid.uuid4(),
                brand=m.get("brand", ""),
                position=_position_str_to_int(m.get("position")),
                confidence=m.get("confidence"),
            )
            session.add(mention_row)
        await session.commit()

    logger.info("Inserted %d Mention rows for response %s", len(mentions_raw), response_id)
    return {
        "response_id": response_id,
        "mentions_found": len(mentions_raw),
        "target_mentions": sum(1 for m in mentions_raw if m.get("is_target_brand")),
        "competitor_mentions": sum(1 for m in mentions_raw if not m.get("is_target_brand")),
        "mentions": mentions_raw,
    }


# ---------------------------------------------------------------------------
# compute_scores_task
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def compute_scores_task(self, project_id: str) -> dict:
    """Recompute visibility scores from DB mentions and insert a new Score row."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_compute_scores_impl(project_id))
        loop.close()
        return result
    except Exception as exc:
        logger.exception("compute_scores_task failed for project %s: %s", project_id, exc)
        raise self.retry(exc=exc)


async def _compute_scores_impl(project_id: str) -> dict:
    logger.info("Computing scores for project=%s", project_id)

    async with AsyncSessionLocal() as session:
        project = await _load_project(session, project_id)
        if not project:
            return {"project_id": project_id, "status": "project_not_found"}

        # Load all prompts for this project to get total_prompts
        prompts_result = await session.execute(
            select(Prompt).where(Prompt.project_id == project_id)
        )
        prompts = prompts_result.scalars().all()
        total_prompts = len(prompts) or 1

        # Load all responses for this project via prompt join
        prompt_ids = [p.id for p in prompts]
        all_mentions = []
        if prompt_ids:
            # Load responses
            responses_result = await session.execute(
                select(Response).where(Response.prompt_id.in_(prompt_ids))
            )
            responses = responses_result.scalars().all()
            response_ids = [r.id for r in responses]

            if response_ids:
                mentions_result = await session.execute(
                    select(Mention).where(Mention.response_id.in_(response_ids))
                )
                all_mentions = mentions_result.scalars().all()

        brand_lower = project.brand_name.lower()
        total_mentions = len(all_mentions)
        brand_mentions = sum(
            1 for m in all_mentions
            if brand_lower in (m.brand or "").lower()
        )

        # Core metric computations
        visibility = brand_mentions / total_prompts if total_prompts > 0 else 0.0
        sov = brand_mentions / total_mentions if total_mentions > 0 else 0.0

        # Intent-weighted impact
        intent_weight_avg = 1.0  # default when no category context available
        avg_confidence = (
            sum(m.confidence or 0.5 for m in all_mentions if brand_lower in (m.brand or "").lower())
            / brand_mentions
            if brand_mentions > 0
            else 0.0
        )
        impact = min(1.0, visibility * intent_weight_avg * avg_confidence)

        # Insert new Score row
        score_row = Score(
            id=uuid.uuid4(),
            project_id=UUID(project_id),
            visibility_score=round(visibility, 4),
            impact_score=round(impact, 4),
            sov_score=round(sov, 4),
            timestamp=datetime.now(timezone.utc),
        )
        session.add(score_row)
        await session.commit()

    score_dict = {
        "project_id": project_id,
        "visibility_score": round(visibility, 4),
        "impact_score": round(impact, 4),
        "sov_score": round(sov, 4),
        "total_prompts": total_prompts,
        "brand_mentions": brand_mentions,
        "total_mentions": total_mentions,
        "status": "completed",
    }
    logger.info("Scores computed for project %s: %s", project_id, score_dict)
    return score_dict


# ---------------------------------------------------------------------------
# cluster_prompts_task
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def cluster_prompts_task(self, project_id: str) -> dict:
    """Group project prompts by category and store clustering summary to Spaces."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_cluster_prompts_impl(project_id))
        loop.close()
        return result
    except Exception as exc:
        logger.exception("cluster_prompts_task failed for project %s: %s", project_id, exc)
        raise self.retry(exc=exc)


async def _cluster_prompts_impl(project_id: str) -> dict:
    logger.info("Clustering prompts for project=%s", project_id)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Prompt).where(Prompt.project_id == project_id)
        )
        prompts = result.scalars().all()

    if not prompts:
        return {"project_id": project_id, "clusters": {}, "total_prompts": 0, "status": "no_prompts"}

    # Group by category
    clusters: dict[str, list] = {}
    for p in prompts:
        cat = p.category or "uncategorized"
        clusters.setdefault(cat, [])
        clusters[cat].append({"id": str(p.id), "text": p.text, "category": cat})

    cluster_summary = {
        cat: {"count": len(items), "sample": items[:3]}
        for cat, items in clusters.items()
    }

    payload = {
        "project_id": project_id,
        "clustered_at": datetime.now(timezone.utc).isoformat(),
        "total_prompts": len(prompts),
        "cluster_count": len(clusters),
        "clusters": cluster_summary,
    }
    try:
        storage.upload_json(
            StorageService.ai_path(project_id, "prompt_clusters.json"),
            payload,
        )
    except Exception as exc:
        logger.warning("Spaces upload failed (non-fatal): %s", exc)

    return {
        "project_id": project_id,
        "total_prompts": len(prompts),
        "cluster_count": len(clusters),
        "clusters": {cat: len(items) for cat, items in clusters.items()},
        "status": "completed",
    }
