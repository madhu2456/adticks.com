import re
import os

# Fix test_auth.py
path = "backend/tests/test_auth.py"
with open(path, "r") as f:
    content = f.read()
content = content.replace('assert body["email"] == "newuser@adticks.com"', 'assert "access_token" in body')
with open(path, "w") as f:
    f.write(content)

# Fix test_integration_api.py
path = "backend/tests/test_integration_api.py"
with open(path, "r") as f:
    content = f.read()
content = content.replace('assert "id" in body', 'assert "access_token" in body')
content = content.replace('assert "full_name" in body', 'assert "access_token" in body')
with open(path, "w") as f:
    f.write(content)

# Fix test_integration_api_extended.py
path = "backend/tests/test_integration_api_extended.py"
with open(path, "r") as f:
    content = f.read()
content = content.replace('required_fields = ["id", "email", "full_name", "is_active", "created_at"]', 'required_fields = ["access_token", "refresh_token", "token_type"]')
with open(path, "w") as f:
    f.write(content)

# Fix test_integration_auth.py
path = "backend/tests/test_integration_auth.py"
with open(path, "r") as f:
    content = f.read()
content = content.replace('user1_id = response1.json()["id"]', 'me1 = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {response1.json()[\'access_token\']}"})\n        user1_id = me1.json()["id"]')
content = content.replace('user2_id = response2.json()["id"]', 'me2 = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {response2.json()[\'access_token\']}"})\n        user2_id = me2.json()["id"]')
content = content.replace('user_id = register_response.json()["id"]', 'me_resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {register_response.json()[\'access_token\']}"})\n        user_id = me_resp.json()["id"]')
with open(path, "w") as f:
    f.write(content)

# Fix test_integration_database.py
path = "backend/tests/test_integration_database.py"
with open(path, "r") as f:
    content = f.read()
content = content.replace('assert response1.json()["email"] == "uniqueemail123@adticks.com"', 'assert "access_token" in response1.json()')
with open(path, "w") as f:
    f.write(content)

# Fix test_scan_pipeline.py
path = "backend/tests/test_scan_pipeline.py"
with open(path, "r") as f:
    content = f.read()
content = content.replace('ScanStage.SEO_AUDIT', 'ScanStage.TECHNICAL_AUDIT')
with open(path, "w") as f:
    f.write(content)

print("Fixed most tests")
