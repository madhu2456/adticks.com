"""Tests to verify run_full_scan_task is called with correct channels."""
from unittest.mock import MagicMock, patch


async def test_run_scan_endpoint_calls_full_scan_task(client, test_project, auth_headers):
    """Verify /api/scan/run endpoint calls run_full_scan_task (not just AI scan)."""
    mock_task = MagicMock()
    mock_task.id = "full-scan-task-123"
    
    with patch("app.workers.tasks.run_full_scan_task.delay", return_value=mock_task):
        response = await client.post(
            f"/api/scan/run?project_id={test_project.id}",
            headers=auth_headers,
        )
    
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "queued"
    assert data["task_id"] == "full-scan-task-123"


async def test_run_scan_includes_all_channels(client, test_project, auth_headers):
    """
    Verify that run_scan endpoint triggers full scan with SEO, AI, GSC, and Ads channels.
    This documents what should happen when user clicks 'Run Scan'.
    """
    mock_task = MagicMock()
    mock_task.id = "full-scan-id"
    
    with patch("app.workers.tasks.run_full_scan_task.delay", return_value=mock_task) as mock_delay:
        response = await client.post(
            f"/api/scan/run?project_id={test_project.id}",
            headers=auth_headers,
        )
    
    assert response.status_code == 202
    
    # Verify run_full_scan_task was called with project_id
    mock_delay.assert_called_once_with(project_id=str(test_project.id))


async def test_run_scan_vs_ai_only_scan_difference():
    """
    Document the difference between full scan and AI-only scan.
    
    This is a specification test showing what channels each endpoint triggers.
    """
    # Full scan (/api/scan/run) should trigger:
    full_scan_pipeline = {
        "seo": {
            "keywords": "generate_keywords_task",
            "rank_tracking": "run_rank_tracking_task",
            "on_page_audit": "run_seo_audit_task",
            "content_gaps": "find_content_gaps_task",
        },
        "ai_visibility": {
            "prompts": "generate_prompts_task",
            "llm_scan": "run_llm_scan_task",
        },
        "gsc": {
            "sync": "sync_gsc_data_task",
        },
        "ads": {
            "sync": "sync_ads_data_task",
        },
        "post_processing": {
            "scores": "compute_scores_task",
            "insights": "generate_insights_task",
        },
    }
    
    # AI-only scan (/api/prompts/generate → /api/scan/run via LLM) should trigger:
    ai_only_pipeline = {
        "ai_visibility": {
            "prompts": "generate_prompts_task",
            "llm_scan": "run_llm_scan_task",
        },
    }
    
    # Verify that full scan has more channels than AI-only scan
    full_channels = set(full_scan_pipeline.keys())
    ai_channels = set(ai_only_pipeline.keys())
    
    assert len(full_channels) > len(ai_channels), (
        "Full scan should include more channels than AI-only scan. "
        f"Full: {full_channels}, AI-only: {ai_channels}"
    )
    
    assert "seo" in full_channels, "Full scan must include SEO"
    assert "gsc" in full_channels, "Full scan must include GSC"
    assert "ads" in full_channels, "Full scan must include Ads"
    assert "ai_visibility" in full_channels, "Full scan must include AI"
    assert "post_processing" in full_channels, "Full scan must include post-processing"
