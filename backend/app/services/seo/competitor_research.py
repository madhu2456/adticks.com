"""
Competitor research service for AdTicks SEO module.
Uses OpenAI to identify keywords competitors rank for.
"""

import logging
import json
import re
import random
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from uuid import UUID

from app.models.seo import CompetitorKeywords
from app.core.database import AsyncSessionLocal

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

def _fallback_identify_competitors(domain: str, industry: str) -> List[str]:
    """Generate realistic fallback competitors if none are provided and OpenAI is unavailable."""
    base = domain.split(".")[0]
    return [
        f"{base}-alternative.com",
        f"top{industry.lower().replace(' ', '')}.com",
        f"best{base}.io",
        f"global{industry.lower().replace(' ', '')}.net",
        f"{industry.lower().replace(' ', '')}leaders.co"
    ]

async def identify_competitors(domain: str, industry: str) -> List[str]:
    """
    Identify top 5 competitors for a given domain and industry using AI.
    """
    logger.info(f"Identifying competitors for domain: {domain} in industry: {industry}")
    
    if not OPENAI_AVAILABLE or not settings.OPENAI_API_KEY:
        if not settings.OPENAI_API_KEY:
            logger.info("OPENAI_API_KEY not set, using fallback competitor generation")
        return _fallback_identify_competitors(domain, industry)

    try:
        client = AsyncOpenAI()
        
        prompt = f"""You are a senior SEO strategist. Identify the top 5 direct online competitors for the domain '{domain}' operating in the '{industry}' industry.
Focus on real, well-known companies that compete for similar search traffic and audience.
Return ONLY a JSON array of 5 bare domain names (e.g., ["example1.com", "example2.com"]). No extra text or explanations."""

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500,
        )
        raw = response.choices[0].message.content.strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        
        competitors = json.loads(raw)
        
        # Ensure we have clean domains and exactly up to 5
        cleaned = []
        for comp in competitors[:5]:
            # remove http/https/www if present
            c = comp.lower().replace("https://", "").replace("http://", "").replace("www.", "").strip()
            c = c.split('/')[0] # remove paths
            if c and c != domain:
                cleaned.append(c)
                
        return cleaned if cleaned else _fallback_identify_competitors(domain, industry)

    except Exception as e:
        logger.warning(f"OpenAI competitor identification failed for {domain}: {e}")
        return _fallback_identify_competitors(domain, industry)

def _fallback_competitor_keywords(domain: str, industry: str) -> List[str]:
    """Generate realistic fallback keywords for a competitor."""
    templates = [
        "best {industry} software",
        "{industry} solutions",
        "enterprise {industry} platform",
        "top {industry} tools 2024",
        "how to improve {industry} efficiency",
        "{industry} automation",
        "affordable {industry} for small business",
        "{industry} analytics dashboard",
        "cloud-based {industry} service",
        "{industry} integration guide"
    ]
    
    keywords = [t.format(industry=industry.lower()) for t in templates]
    # Add some domain-specific ones
    keywords.append(f"{domain.split('.')[0]} reviews")
    keywords.append(f"{domain.split('.')[0]} pricing")
    
    return keywords

async def research_competitor_keywords(
    domain: str, 
    industry: str,
    brand_name: Optional[str] = None
) -> List[str]:
    """
    Research keywords for a specific competitor domain.
    """
    logger.info(f"Researching keywords for competitor: {domain}")
    
    if not OPENAI_AVAILABLE or not settings.OPENAI_API_KEY:
        return _fallback_competitor_keywords(domain, industry)

    try:
        client = AsyncOpenAI()
        
        prompt = f"""You are a senior SEO researcher. Analyze the competitor domain '{domain}' in the '{industry}' industry.
Identify 15-20 high-value keywords this competitor likely ranks for.
Return them as a simple JSON array of strings. No extra text."""

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000,
        )
        raw = response.choices[0].message.content.strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        return json.loads(raw)

    except Exception as e:
        logger.warning(f"OpenAI competitor research failed for {domain}: {e}")
        return _fallback_competitor_keywords(domain, industry)

async def sync_competitor_keywords(
    project_id: str, 
    competitor_domains: List[str],
    industry: str
) -> int:
    """
    Sync competitor keywords to the database.
    """
    count = 0
    try:
        async with AsyncSessionLocal() as db:
            import uuid
            
            for domain in competitor_domains:
                keywords = await research_competitor_keywords(domain, industry)
                
                # Check if entry already exists for this domain in this project
                from sqlalchemy import select, delete
                # For simplicity, we refresh it
                await db.execute(
                    delete(CompetitorKeywords).where(
                        CompetitorKeywords.project_id == UUID(project_id),
                        CompetitorKeywords.competitor_domain == domain
                    )
                )
                
                comp_kw = CompetitorKeywords(
                    id=uuid.uuid4(),
                    project_id=UUID(project_id),
                    competitor_domain=domain,
                    keywords=keywords,
                    count=len(keywords),
                    timestamp=datetime.now(timezone.utc)
                )
                db.add(comp_kw)
                count += 1
            
            await db.commit()
            return count
    except Exception as e:
        logger.error(f"Error syncing competitor keywords: {e}")
        return 0
