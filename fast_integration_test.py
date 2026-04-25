import httpx
import asyncio
import uuid
import time

BASE_URL = "http://localhost:8002/api"

async def test_full_integration():
    print("🚀 Starting Fast API Integration Test...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Register
        random_id = str(uuid.uuid4())[:8]
        email = f"api-test-{random_id}@example.com"
        password = "TestPassword123!"
        
        print(f"📝 Registering {email}...")
        resp = await client.post(f"{BASE_URL}/auth/register", json={
            "email": email,
            "password": password,
            "full_name": "API Tester"
        })
        assert resp.status_code == 201, f"Register failed: {resp.text}"
        print("✅ Registration successful")

        # 2. Login
        print("🔑 Logging in...")
        resp = await client.post(f"{BASE_URL}/auth/login", json={
            "email": email,
            "password": password
        })
        assert resp.status_code == 200
        tokens = resp.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        print("✅ Login successful")

        # 3. Create Project
        print("📂 Creating project...")
        resp = await client.post(f"{BASE_URL}/projects", headers=headers, json={
            "brand_name": f"API Project {random_id}",
            "domain": f"api-{random_id}.com",
            "industry": "SaaS / Software"
        })
        assert resp.status_code == 201
        project_id = resp.json()["id"]
        print(f"✅ Project created: {project_id}")

        # 4. Run Scan (Background Task)
        print("🔍 Starting SEO Scan...")
        # Trying /ai/scan/run based on router mounting
        resp = await client.post(f"{BASE_URL}/ai/scan/run?project_id={project_id}", headers=headers)
        if resp.status_code == 404:
            print("   ⚠️ /api/ai/scan/run failed, trying /api/scan/run...")
            resp = await client.post(f"{BASE_URL}/scan/run?project_id={project_id}", headers=headers)
            
        if resp.status_code != 202:
            print(f"❌ Scan trigger failed ({resp.status_code}): {resp.text}")
        assert resp.status_code == 202
        task_id = resp.json()["task_id"]
        print(f"✅ Scan queued: {task_id}")

        # 5. Check Progress (WebSocket-like polling)
        print(f"⏳ Monitoring progress for task_id: {task_id}...")
        print("   (Waiting 5s for task to start in Celery...)")
        await asyncio.sleep(5)
        
        for i in range(15):
            resp = await client.get(f"{BASE_URL}/ws/scan/progress/{task_id}", headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                status = data.get('status')
                progress = data.get('progress')
                message = data.get('message')
                print(f"   📊 [{i}] Progress: {progress}% - {message} (Status: {status})")
                if progress == 100 or status == 'completed':
                    print("✅ Scan completed successfully!")
                    break
            else:
                print(f"   ⚠️ [{i}] Progress endpoint returned {resp.status_code}")
            await asyncio.sleep(3)
        
        print("\n✨ Fast Integration Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_full_integration())
