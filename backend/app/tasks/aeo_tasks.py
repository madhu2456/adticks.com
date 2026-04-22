"""
Background tasks for AEO module.

Handles asynchronous visibility checks and data collection.
"""

from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.keyword import Keyword
from app.models.aeo import AEOVisibility, AEOTrends
from app.services.ai_visibility import AIVisibilityService
from app.core.logging import get_logger

logger = get_logger(__name__)


async def check_keyword_visibility(
    db: AsyncSession,
    project_id: UUID,
    keyword_id: UUID,
    brand_name: str,
    domain: str,
    ai_models: list[str] = None
):
    """
    Check visibility of a keyword across AI models.
    
    This would be called by a background task (Celery, APScheduler, etc.)
    """
    if ai_models is None:
        ai_models = ["chatgpt", "perplexity", "claude"]

    service = AIVisibilityService()

    try:
        # Get keyword
        from sqlalchemy import select
        result = await db.execute(
            select(Keyword).where(Keyword.id == keyword_id)
        )
        keyword = result.scalar_one_or_none()

        if not keyword:
            logger.warning("keyword_not_found", extra={"keyword_id": str(keyword_id)})
            return

        keyword_text = keyword.keyword

        # Check each AI model
        for model in ai_models:
            try:
                if model == "chatgpt":
                    is_mentioned, context, position, confidence = await service.check_chatgpt_visibility(
                        keyword_text, brand_name, domain
                    )
                elif model == "perplexity":
                    is_mentioned, context, position, confidence = await service.check_perplexity_visibility(
                        keyword_text, brand_name, domain
                    )
                elif model == "claude":
                    is_mentioned, context, position, confidence = await service.check_claude_visibility(
                        keyword_text, brand_name, domain
                    )
                else:
                    logger.warning("unknown_ai_model", extra={"model": model})
                    continue

                # Store result
                await service.store_visibility_check(
                    db=db,
                    project_id=project_id,
                    keyword_id=keyword_id,
                    ai_model=model,
                    is_mentioned=is_mentioned,
                    mention_context=context,
                    position=position,
                    confidence_score=confidence
                )

                # Calculate trends
                await service.calculate_trends(db, project_id, keyword_id, model)

                logger.info("visibility_check_completed", extra={
                    "keyword": keyword_text,
                    "model": model,
                    "mentioned": is_mentioned
                })

            except Exception as e:
                logger.error("visibility_check_failed", extra={
                    "keyword": keyword_text,
                    "model": model,
                    "error": str(e)
                })
                continue

        await db.commit()

    except Exception as e:
        logger.error("check_keyword_visibility_failed", extra={"error": str(e)})
        await db.rollback()


async def daily_visibility_check(
    db: AsyncSession,
    project_id: UUID,
    brand_name: str,
    domain: str
):
    """
    Daily background task to check visibility for all keywords in a project.
    """
    try:
        from sqlalchemy import select

        # Get all keywords for project
        result = await db.execute(
            select(Keyword).where(Keyword.project_id == project_id)
        )
        keywords = result.scalars().all()

        logger.info("daily_visibility_check_started", extra={
            "project_id": str(project_id),
            "keyword_count": len(keywords)
        })

        for keyword in keywords:
            await check_keyword_visibility(
                db, project_id, keyword.id, brand_name, domain
            )

        logger.info("daily_visibility_check_completed", extra={
            "project_id": str(project_id)
        })

    except Exception as e:
        logger.error("daily_visibility_check_failed", extra={"error": str(e)})
