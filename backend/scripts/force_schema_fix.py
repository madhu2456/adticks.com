import asyncio
import logging
from sqlalchemy import text
from app.core.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def force_fix():
    logger.info("Starting force schema fix...")
    
    async with engine.begin() as conn:
        # 1. Create clusters table if missing
        logger.info("Checking for clusters table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS clusters (
                id UUID PRIMARY KEY,
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                topic_name VARCHAR(512) NOT NULL,
                keywords JSONB NOT NULL DEFAULT '[]',
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
        """))
        
        # 2. Add cluster_id to keywords if missing
        logger.info("Checking for keywords.cluster_id column...")
        await conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='keywords' AND column_name='cluster_id') THEN
                    ALTER TABLE keywords ADD COLUMN cluster_id UUID REFERENCES clusters(id) ON DELETE SET NULL;
                    CREATE INDEX ix_keywords_cluster_id ON keywords (cluster_id);
                END IF;
            END
            $$;
        """))
        
        # 3. Fix backlinks table columns
        logger.info("Checking for backlinks columns...")
        await conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='backlinks' AND column_name='target_url') THEN
                    ALTER TABLE backlinks ADD COLUMN target_url VARCHAR(2048);
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='backlinks' AND column_name='anchor_text') THEN
                    ALTER TABLE backlinks ADD COLUMN anchor_text VARCHAR(1024);
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='backlinks' AND column_name='authority_score') THEN
                    ALTER TABLE backlinks ADD COLUMN authority_score FLOAT NOT NULL DEFAULT 0.0;
                END IF;
            END
            $$;
        """))

    logger.info("Force schema fix completed.")

if __name__ == "__main__":
    asyncio.run(force_fix())
