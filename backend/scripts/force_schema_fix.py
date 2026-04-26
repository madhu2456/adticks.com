import asyncio
import logging
from sqlalchemy import text
from app.core.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def force_fix():
    logger.info("Starting comprehensive force schema fix...")
    
    async with engine.begin() as conn:
        # --- 1. Clusters Table ---
        logger.info("Ensuring clusters table exists...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS clusters (
                id UUID PRIMARY KEY,
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                topic_name VARCHAR(512) NOT NULL,
                keywords JSONB NOT NULL DEFAULT '[]',
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
        """))
        
        # --- 2. Keywords Table Columns ---
        logger.info("Ensuring keywords table columns exist...")
        await conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='keywords' AND column_name='cluster_id') THEN
                    ALTER TABLE keywords ADD COLUMN cluster_id UUID REFERENCES clusters(id) ON DELETE SET NULL;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='keywords' AND column_name='intent') THEN
                    ALTER TABLE keywords ADD COLUMN intent VARCHAR(64);
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='keywords' AND column_name='difficulty') THEN
                    ALTER TABLE keywords ADD COLUMN difficulty FLOAT;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='keywords' AND column_name='volume') THEN
                    ALTER TABLE keywords ADD COLUMN volume INTEGER;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='keywords' AND column_name='search_volume_history') THEN
                    ALTER TABLE keywords ADD COLUMN search_volume_history JSONB;
                END IF;
            END
            $$;
        """))

        # --- 3. Rankings Table Columns ---
        logger.info("Ensuring rankings table columns exist...")
        await conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='rankings' AND column_name='position') THEN
                    ALTER TABLE rankings ADD COLUMN position INTEGER;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='rankings' AND column_name='url') THEN
                    ALTER TABLE rankings ADD COLUMN url VARCHAR(2048);
                END IF;
            END
            $$;
        """))
        
        # --- 4. Backlinks Table Columns ---
        logger.info("Ensuring backlinks table columns exist...")
        await conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='backlinks') THEN
                    CREATE TABLE backlinks (
                        id UUID PRIMARY KEY,
                        project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                        referring_domain VARCHAR(255) NOT NULL,
                        target_url VARCHAR(2048),
                        anchor_text VARCHAR(1024),
                        status VARCHAR(32) NOT NULL DEFAULT 'active',
                        authority_score FLOAT NOT NULL DEFAULT 0.0,
                        first_seen TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                        last_seen TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                        timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                    );
                ELSE
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='backlinks' AND column_name='target_url') THEN
                        ALTER TABLE backlinks ADD COLUMN target_url VARCHAR(2048);
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='backlinks' AND column_name='anchor_text') THEN
                        ALTER TABLE backlinks ADD COLUMN anchor_text VARCHAR(1024);
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='backlinks' AND column_name='authority_score') THEN
                        ALTER TABLE backlinks ADD COLUMN authority_score FLOAT NOT NULL DEFAULT 0.0;
                    END IF;
                END IF;
            END
            $$;
        """))

        # --- 5. Project Table Columns ---
        logger.info("Ensuring projects table columns exist...")
        await conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='projects' AND column_name='gsc_connected') THEN
                    ALTER TABLE projects ADD COLUMN gsc_connected BOOLEAN NOT NULL DEFAULT FALSE;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='projects' AND column_name='gsc_property_url') THEN
                    ALTER TABLE projects ADD COLUMN gsc_property_url VARCHAR(512);
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='projects' AND column_name='ai_scans_enabled') THEN
                    ALTER TABLE projects ADD COLUMN ai_scans_enabled BOOLEAN NOT NULL DEFAULT TRUE;
                END IF;
            END
            $$;
        """))

        # --- 6. Users Table Columns ---
        logger.info("Ensuring users table columns exist...")
        await conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='plan') THEN
                    ALTER TABLE users ADD COLUMN plan VARCHAR(32) NOT NULL DEFAULT 'free';
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='company_name') THEN
                    ALTER TABLE users ADD COLUMN company_name VARCHAR(255);
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='is_superuser') THEN
                    ALTER TABLE users ADD COLUMN is_superuser BOOLEAN NOT NULL DEFAULT FALSE;
                END IF;
            END
            $$;
        """))

    logger.info("Force schema fix completed.")

if __name__ == "__main__":
    asyncio.run(force_fix())
