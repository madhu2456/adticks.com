import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.seo.content_gap_analyzer import find_gaps

async def main():
    project_keywords = ["seo software", "keyword tracking"]
    competitor_domains = ["ahrefs.com", "semrush.com"]
    industry = "Technology"
    brand_name = "testbrand"
    
    gaps = await find_gaps(
        project_keywords=project_keywords,
        competitor_domains=competitor_domains,
        industry=industry,
        brand_name=brand_name
    )
    print("Gaps found:")
    print(gaps)

if __name__ == "__main__":
    asyncio.run(main())
