#!/usr/bin/env python3
"""
Test script to trigger a scan and monitor progress until completion.
"""
import asyncio
import json
import time
import sys
from datetime import datetime
import aiohttp
from pathlib import Path

# Load env to get API URL
env_file = Path(__file__).parent / "backend" / ".env"
env_vars = {}
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                k, v = line.strip().split('=', 1)
                env_vars[k] = v

API_URL = "http://localhost:8002/api"
MAX_WAIT = 600  # 10 minutes max wait

async def get_projects():
    """Get all projects."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/projects", headers={"Authorization": "Bearer test"}) as resp:
            if resp.status == 200:
                return await resp.json()
    return []

async def start_scan(project_id):
    """Start a full scan."""
    async with aiohttp.ClientSession() as session:
        # Note: In the actual API, project_id is a query parameter for /api/scan/run
        async with session.post(
            f"{API_URL}/scan/run?project_id={project_id}&force_refresh=true",
            headers={"Authorization": "Bearer test"}
        ) as resp:
            if resp.status == 202:  # Accepted
                return await resp.json()
            else:
                text = await resp.text()
                print(f"❌ Failed to start scan: {resp.status} - {text}")
    return None

async def get_scan_status(task_id):
    """Get scan status by task ID."""
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{API_URL}/scan/status/{task_id}",
            headers={"Authorization": "Bearer test"}
        ) as resp:
            if resp.status == 200:
                return await resp.json()
    return None

async def monitor_scan(task_id, max_wait=MAX_WAIT):
    """Monitor a scan until completion."""
    print(f"\n📊 Monitoring scan {task_id}")
    print("=" * 60)
    
    start_time = time.time()
    last_progress = -1
    
    while time.time() - start_time < max_wait:
        status = await get_scan_status(task_id)
        
        if not status:
            print("❌ Could not fetch status")
            await asyncio.sleep(5)
            continue
        
        progress = status.get('progress', 0)
        stage = status.get('stage', 'unknown')
        message = status.get('message', '')
        elapsed = status.get('elapsed_seconds', 0)
        
        # Only print if progress changed
        if progress != last_progress:
            elapsed_min = elapsed // 60
            elapsed_sec = elapsed % 60
            print(f"⏱  [{elapsed_min}m {elapsed_sec}s] {progress}% | {stage} | {message}")
            last_progress = progress
        
        # Check for completion
        if progress >= 100:
            elapsed_total = time.time() - start_time
            print("=" * 60)
            print(f"✅ SCAN COMPLETED in {elapsed_total:.1f}s!")
            print(f"   Final status: {status.get('status', 'unknown')}")
            return True
        
        await asyncio.sleep(2)
    
    print("=" * 60)
    print(f"⏱  TIMEOUT: Scan did not complete within {max_wait}s")
    status = await get_scan_status(task_id)
    if status:
        print(f"   Last progress: {status.get('progress', 0)}%")
        print(f"   Stage: {status.get('stage', 'unknown')}")
    return False

async def main():
    print("🚀 AdTicks Scan Test")
    print("=" * 60)
    
    # Get projects
    print("\n📋 Fetching projects...")
    projects = await get_projects()
    
    if not projects:
        print("❌ No projects found!")
        return False
    
    project = projects[0]
    project_id = project.get('id')
    print(f"✓ Found project: {project.get('domain')} ({project_id})")
    
    # Start scan
    print(f"\n🔄 Starting full scan...")
    scan_result = await start_scan(project_id)
    
    if not scan_result:
        print("❌ Failed to start scan")
        return False
    
    task_id = scan_result.get('task_id') or scan_result.get('id')
    print(f"✓ Scan started: {task_id}")
    
    # Monitor scan
    success = await monitor_scan(task_id)
    
    return success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
