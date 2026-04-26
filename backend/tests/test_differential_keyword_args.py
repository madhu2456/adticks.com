
import pytest
from app.core.differential_updates import DifferentialUpdateDetector

@pytest.mark.asyncio
async def test_keyword_arguments():
    """Test that DifferentialUpdateDetector methods accept correct keyword arguments."""
    project_id = "test-kw-args"
    detector = DifferentialUpdateDetector(project_id)
    
    domain = "example.com"
    keywords = ["seo", "marketing"]
    competitors = ["comp1.com", "comp2.com"]
    
    # Test get_changes_summary with keyword arguments
    # This was failing because 'competitors' was named 'competitor_domains' in signature
    summary = await detector.get_changes_summary(
        domain=domain,
        keywords=keywords,
        competitors=competitors
    )
    assert "requires_full_rescan" in summary
    
    # Test save_all_states with keyword arguments
    await detector.save_all_states(
        domain=domain,
        keywords=keywords,
        competitors=competitors
    )
    
    # Test individual changed methods with keyword arguments
    await detector.keywords_changed(keywords=keywords)
    await detector.domain_changed(domain=domain)
    await detector.competitors_changed(competitors=competitors)
    
    # Clean up
    await detector.clear_states()
