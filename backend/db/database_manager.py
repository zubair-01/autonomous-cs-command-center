import asyncio
from typing import AsyncGenerator
from lib.config_loader import config_loader
from models.schemas import Base
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from utils.log import logger


class DatabaseManager:
    """
    OOP Database Manager responsible for asynchronous PostgreSQL connection pools,
    pgvector extension initialization, schema migrations, and session generation.
    """

    def __init__(self):
        self.db_url = config_loader.database_url
        self.engine: AsyncEngine = create_async_engine(
            self.db_url,
            echo=False,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True
        )
        self.async_session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def init_db(self) -> None:
        """
        Initializes the PostgreSQL database:
        1. Enables the pgvector extension.
        2. Creates all ORM tables (customers, tickets, agent_logs, doc_embeddings).
        """
        logger.info("Initializing PostgreSQL database and pgvector extension...")
        try:
            async with self.engine.begin() as conn:
                # 1. Enable pgvector extension inside PostgreSQL
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                logger.info("pgvector extension verified/enabled successfully.")

                # 2. Create all defined SQLAlchemy tables
                await conn.run_sync(Base.metadata.create_all)
                logger.info("Database tables created successfully.")
        except Exception as e:
            logger.error(f"Error during database initialization: {e}")
            raise e

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Async generator yielding database session context."""
        async with self.async_session_factory() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {e}")
                raise e
            finally:
                await session.close()


# Global singleton instance of DatabaseManager
db_manager = DatabaseManager()
