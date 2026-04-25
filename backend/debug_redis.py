import asyncio
import logging
from app.core.progress import ScanProgress

logging.basicConfig(level=logging.DEBUG)

async def test_redis_progress():
    task_id = "debug-task-123"
    project_id = "debug-project-123"
    
    print(f"🚀 Testing Redis Progress for task: {task_id}")
    
    progress = ScanProgress(project_id, task_id)
    print("⏳ Initializing...")
    await progress.initialize()
    
    print("⏳ Updating...")
    await progress.update("test_stage", 50, "Testing message")
    
    print("🔍 Fetching...")
    res = await ScanProgress.get_progress_for_task(task_id)
    print(f"✅ Result: {res}")
    
    if res and res.get('progress') == 50:
        print("🎉 SUCCESS: Redis progress working correctly!")
    else:
        print("❌ FAILURE: Redis progress NOT working.")

if __name__ == "__main__":
    asyncio.run(test_redis_progress())
