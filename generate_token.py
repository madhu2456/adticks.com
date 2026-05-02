import asyncio
import sys
sys.path.insert(0, 'F:\\Codes\\Claude\\Adticks\\backend')

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import create_access_token
from sqlalchemy import select

async def get_token():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        if user:
            # Correct: pass just the user ID string
            token = create_access_token(str(user.id))
            print(f'User: {user.email}')
            print(f'UserId: {user.id}')
            print(f'Token: {token}')
        else:
            print('No users found')

asyncio.run(get_token())
