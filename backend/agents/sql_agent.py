import asyncio
import datetime
from typing import Any, Dict
from agents.state import TicketState
from db.database_manager import db_manager
from models.schemas import CustomerModel
from sqlalchemy.future import select
from utils.log import logger


class SQLAgent:
    """
    OOP SQL Agent responsible for querying customer account details,
    subscription plan tiers, and guaranteed SLA parameters from PostgreSQL.
    """

    def __init__(self):
        self.db_manager = db_manager

    async def execute_lookup_async(self, state: TicketState) -> Dict[str, Any]:
        """
        Asynchronously queries PostgreSQL for customer account and SLA data.
        """
        customer_email = state["customer_email"]
        logger.info(f"[SQLAgent] Executing PostgreSQL customer query for: {customer_email}")

        sql_result = {
            "customer_id": state.get("customer_id"),
            "customer_name": state.get("customer_name"),
            "plan_tier": state.get("plan_tier", "Standard"),
            "sla_hours": state.get("sla_hours", 24),
            "account_status": "ACTIVE",
            "is_enterprise_sla": state.get("plan_tier") == "Enterprise",
            "query_timestamp": datetime.datetime.utcnow().isoformat()
        }

        try:
            async with self.db_manager.async_session_factory() as session:
                result = await session.execute(
                    select(CustomerModel).where(CustomerModel.email == customer_email)
                )
                customer = result.scalars().first()

                if customer:
                    sql_result.update({
                        "customer_id": customer.id,
                        "customer_name": customer.name,
                        "plan_tier": customer.plan_tier,
                        "sla_hours": customer.sla_hours,
                        "is_enterprise_sla": customer.plan_tier == "Enterprise"
                    })
                    logger.info(f"[SQLAgent] PostgreSQL lookup success: {customer.name} ({customer.plan_tier} Plan, {customer.sla_hours}h SLA)")
        except Exception as e:
            logger.warning(f"[SQLAgent] Async DB query warning, using state fallback: {e}")

        return {"sql_data": sql_result}

    def execute_lookup(self, state: TicketState) -> Dict[str, Any]:
        """Synchronous wrapper for LangGraph node execution."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If running inside existing asyncio loop
                return asyncio.run_coroutine_threadsafe(self.execute_lookup_async(state), loop).result()
            else:
                return loop.run_until_complete(self.execute_lookup_async(state))
        except Exception:
            return asyncio.run(self.execute_lookup_async(state))
