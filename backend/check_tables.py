import asyncio
from sqlalchemy import inspect
from app.core.database import engine

async def check():
    async with engine.connect() as conn:
        tables = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())
        print("Existing tables:", tables)

if __name__ == "__main__":
    asyncio.run(check())
