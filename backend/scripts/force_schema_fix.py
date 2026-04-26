import asyncio
import logging
from sqlalchemy import text
from app.core.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def force_fix():
    logger.info("Starting robust force schema fix (v2)...")
    
    async with engine.begin() as conn:
        # --- 1. Clusters Table ---
        logger.info("Ensuring clusters table exists...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS public.clusters (
                id UUID PRIMARY KEY,
                project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
                topic_name VARCHAR(512) NOT NULL,
                keywords JSONB NOT NULL DEFAULT '[]',
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
        """))
        
        # --- 2. Keywords Table Columns ---
        logger.info("Ensuring keywords table columns exist...")
        await conn.execute(text("""
            ALTER TABLE public.keywords ADD COLUMN IF NOT EXISTS cluster_id UUID REFERENCES public.clusters(id) ON DELETE SET NULL;
            ALTER TABLE public.keywords ADD COLUMN IF NOT EXISTS intent VARCHAR(64);
            ALTER TABLE public.keywords ADD COLUMN IF NOT EXISTS difficulty FLOAT;
            ALTER TABLE public.keywords ADD COLUMN IF NOT EXISTS volume INTEGER;
            ALTER TABLE public.keywords ADD COLUMN IF NOT EXISTS search_volume_history JSONB;
        """))

        # --- 3. Rankings Table Columns ---
        logger.info("Ensuring rankings table columns exist...")
        await conn.execute(text("""
            ALTER TABLE public.rankings ADD COLUMN IF NOT EXISTS position INTEGER;
            ALTER TABLE public.rankings ADD COLUMN IF NOT EXISTS url VARCHAR(2048);
        """))
        
        # --- 4. Backlinks Table ---
        logger.info("Ensuring backlinks table and columns exist...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS public.backlinks (
                id UUID PRIMARY KEY,
                project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
                referring_domain VARCHAR(255) NOT NULL,
                target_url VARCHAR(2048),
                anchor_text VARCHAR(1024),
                status VARCHAR(32) NOT NULL DEFAULT 'active',
                authority_score FLOAT NOT NULL DEFAULT 0.0,
                first_seen TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                last_seen TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
            
            ALTER TABLE public.backlinks ADD COLUMN IF NOT EXISTS target_url VARCHAR(2048);
            ALTER TABLE public.backlinks ADD COLUMN IF NOT EXISTS anchor_text VARCHAR(1024);
            ALTER TABLE public.backlinks ADD COLUMN IF NOT EXISTS authority_score FLOAT NOT NULL DEFAULT 0.0;
        """))

        # --- 5. Project Table Columns ---
        logger.info("Ensuring projects table columns exist...")
        await conn.execute(text("""
            ALTER TABLE public.projects ADD COLUMN IF NOT EXISTS gsc_connected BOOLEAN NOT NULL DEFAULT FALSE;
            ALTER TABLE public.projects ADD COLUMN IF NOT EXISTS gsc_property_url VARCHAR(512);
            ALTER TABLE public.projects ADD COLUMN IF NOT EXISTS ai_scans_enabled BOOLEAN NOT NULL DEFAULT TRUE;
        """))

        # --- 6. Users Table Columns ---
        logger.info("Ensuring users table columns exist...")
        await conn.execute(text("""
            ALTER TABLE public.users ADD COLUMN IF NOT EXISTS plan VARCHAR(32) NOT NULL DEFAULT 'free';
            ALTER TABLE public.users ADD COLUMN IF NOT EXISTS company_name VARCHAR(255);
            ALTER TABLE public.users ADD COLUMN IF NOT EXISTS is_superuser BOOLEAN NOT NULL DEFAULT FALSE;
        """))

    logger.info("Force schema fix v2 completed.")

if __name__ == "__main__":
    asyncio.run(force_fix())
