import random
from db.database_manager import db_manager
from models.schemas import CustomerModel, DocEmbeddingModel
from sqlalchemy.future import select
from utils.log import logger


class SeedManager:
    """
    OOP Seed Manager responsible for populating initial customer records
    and technical documentation wiki embeddings into pgvector.
    """

    def __init__(self):
        self.db_manager = db_manager

    @staticmethod
    def _generate_mock_embedding(dim: int = 1536, seed_val: float = 0.1) -> list:
        """Generates a deterministic 1536-dimensional normalized vector embedding."""
        random.seed(seed_val)
        raw_vec = [random.uniform(-1.0, 1.0) for _ in range(dim)]
        # Normalize vector length to 1.0 for cosine similarity
        norm = sum(x ** 2 for x in raw_vec) ** 0.5
        return [x / norm for x in raw_vec]

    async def seed_data(self) -> None:
        """Populates customers and doc embeddings if database is empty."""
        logger.info("Checking if database seeding is required...")

        async with self.db_manager.async_session_factory() as session:
            # 1. Seed Customer Accounts
            result = await session.execute(select(CustomerModel))
            existing_customers = result.scalars().all()

            if not existing_customers:
                logger.info("Seeding customer accounts...")
                customers = [
                    CustomerModel(
                        name="Alice Smith (Acme Corp)",
                        email="alice@acme.com",
                        plan_tier="Enterprise",
                        sla_hours=2
                    ),
                    CustomerModel(
                        name="Bob Jones (Startup Inc)",
                        email="bob@startup.io",
                        plan_tier="Pro",
                        sla_hours=8
                    ),
                    CustomerModel(
                        name="Charlie Brown (Tech Labs)",
                        email="charlie@techlabs.dev",
                        plan_tier="Standard",
                        sla_hours=24
                    ),
                ]
                session.add_all(customers)
                await session.commit()
                logger.info("Customer accounts seeded successfully.")
            else:
                logger.info(f"Database already contains {len(existing_customers)} customers. Skipping customer seed.")

            # 2. Seed Technical Wiki Docs (pgvector)
            result = await session.execute(select(DocEmbeddingModel))
            existing_docs = result.scalars().all()

            if not existing_docs:
                logger.info("Seeding technical documentation wiki into pgvector...")
                wiki_docs = [
                    DocEmbeddingModel(
                        title="Resolving PostgreSQL 504 Gateway Timeouts in Enterprise API",
                        category="Infrastructure & DB",
                        content=(
                            "If enterprise clients experience 504 Gateway Timeouts during peak traffic, "
                            "check connection pool size in config.properties. Ensure pgvector pool size is set to 20 "
                            "and max_overflow is at 40. Enable asyncpg keepalives in PostgreSQL."
                        ),
                        embedding=self._generate_mock_embedding(seed_val=1.0)
                    ),
                    DocEmbeddingModel(
                        title="Billing Upgrade & Enterprise SLA Guarantee Policy",
                        category="Billing & SLA",
                        content=(
                            "Enterprise Plan accounts guarantee a 2-hour SLA response time. "
                            "Pro tier guarantees an 8-hour SLA. Standard tier guarantees 24 hours. "
                            "Upgrades take effect immediately upon credit card charge approval."
                        ),
                        embedding=self._generate_mock_embedding(seed_val=2.0)
                    ),
                    DocEmbeddingModel(
                        title="API Rate Limits and Webhook Re-delivery Guide",
                        category="API Operations",
                        content=(
                            "API endpoints enforce a rate limit of 1,000 requests/min per IP. "
                            "Webhooks that fail with 5xx status codes are retried automatically with exponential backoff "
                            "at intervals of 1m, 5m, and 15m up to 5 attempts."
                        ),
                        embedding=self._generate_mock_embedding(seed_val=3.0)
                    ),
                ]
                session.add_all(wiki_docs)
                await session.commit()
                logger.info("Technical documentation wiki seeded successfully.")
            else:
                logger.info(f"Database already contains {len(existing_docs)} documentation chunks. Skipping doc seed.")


# Global singleton instance of SeedManager
seed_manager = SeedManager()
