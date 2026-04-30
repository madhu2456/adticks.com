"""
Backlink analysis service for AdTicks.
Analyzes backlinks and domain authority for projects.
"""

import logging
import random
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from uuid import UUID

from app.models.seo import Backlinks
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

async def analyze_backlinks(project_id: str, domain: str) -> List[Dict[str, Any]]:
    """
    Perform backlink analysis for a domain.
    Returns a list of backlink dicts.
    """
    logger.info(f"Analyzing backlinks for {domain}")
    
    # In a real app, this would call Ahrefs/Moz/Majestic API
    # Here we generate realistic simulated data
    
    backlinks = []
    
    # Generate 15-30 backlinks
    count = random.randint(15, 30)
    
    link_types = ["blog post", "news article", "directory", "resource page", "forum"]
    statuses = ["active", "active", "active", "active", "lost"]
    
    # Common referring domains based on industry could be added here
    
    for i in range(count):
        authority = random.randint(10, 95)
        days_ago = random.randint(1, 90)
        timestamp = datetime.now(timezone.utc) - timedelta(days=days_ago)
        
        status = random.choice(statuses)
        
        backlinks.append({
            "referring_domain": f"site-{i+1}.{random.choice(['com', 'org', 'net', 'io'])}",
            "target_url": f"https://{domain}/" + (random.choice(["", "blog", "about", "product"]) if random.random() > 0.5 else ""),
            "anchor_text": random.choice(["click here", domain, "best solution", "learn more", "SEO tool"]),
            "authority_score": float(authority),
            "status": status,
            "first_seen": timestamp,
            "last_seen": datetime.now(timezone.utc) if status == "active" else timestamp + timedelta(days=random.randint(1, 30))
        })
    
    return backlinks

async def sync_backlinks(project_id: str, domain: str) -> int:
    """
    Sync backlinks to the database.
    """
    try:
        backlink_data = await analyze_backlinks(project_id, domain)
        
        async with AsyncSessionLocal() as db:
            # For simplicity, we just add new ones for now
            # In production we'd do a proper upsert
            import uuid
            
            new_links = []
            for item in backlink_data:
                link = Backlinks(
                    id=uuid.uuid4(),
                    project_id=UUID(project_id),
                    referring_domain=item["referring_domain"],
                    target_url=item["target_url"],
                    anchor_text=item["anchor_text"],
                    authority_score=item["authority_score"],
                    status=item["status"],
                    first_seen=item["first_seen"],
                    last_seen=item["last_seen"],
                    timestamp=datetime.now(timezone.utc)
                )
                db.add(link)
                new_links.append(link)
            
            await db.commit()
            return len(new_links)
    except Exception as e:
        logger.error(f"Error syncing backlinks: {e}")
        return 0
