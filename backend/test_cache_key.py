import asyncio
import os
import sys
import uuid
import json

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.core.caching import cache_key

class MockUser:
    def __init__(self):
        self.id = uuid.uuid4()

user = MockUser()
project_id1 = uuid.uuid4()
project_id2 = uuid.uuid4()

print("Project 1 key:", cache_key(project_id=project_id1, skip=0, limit=50, current_user=user))
print("Project 2 key:", cache_key(project_id=project_id2, skip=0, limit=50, current_user=user))

