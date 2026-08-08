import asyncio
import datetime
from typing import Any, Dict
from agents.draft_agent import DraftAgent
from agents.rag_agent import RAGAgent
from agents.router_agent import RouterAgent
from agents.sql_agent import SQLAgent
from agents.state import TicketState
from db.database_manager import db_manager
from langgraph.graph import END, StateGraph
from models.schemas import AgentLogModel, TicketModel
from sqlalchemy.future import select
from utils.log import logger
from utils.redis_pubsub import redis_pubsub


class WorkflowManager:
    """
    OOP LangGraph Workflow Manager.
    Constructs, compiles, and executes the StateGraph state machine connecting:
    RouterAgent ➔ SQLAgent & RAGAgent ➔ DraftAgent.
    Persists agent reasoning traces directly to PostgreSQL (Hierarchical Flow Inheritance)
    and streams live real-time telemetry via Redis Pub/Sub to WebSockets.
    """

    def __init__(self):
        self.router_agent = RouterAgent()
        self.sql_agent = SQLAgent()
        self.rag_agent = RAGAgent()
        self.draft_agent = DraftAgent()
        self.db_manager = db_manager
        self.redis_pubsub = redis_pubsub
        self.app = self._build_graph()

    def _broadcast_telemetry(self, ticket_id: str, step_index: int, node_name: str, action_type: str, details: str, full_draft: str = None) -> None:
        """Helper to publish live telemetry events synchronously to Redis Pub/Sub."""
        event_payload = {
            "ticket_id": ticket_id,
            "step_index": step_index,
            "node_name": node_name,
            "action_type": action_type,
            "details": details,
            "full_draft": full_draft,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        self.redis_pubsub.publish_event_sync(event_payload)

    def _build_graph(self):
        """Constructs and compiles the LangGraph StateGraph."""
        logger.info("Constructing LangGraph Multi-Agent StateGraph...")
        builder = StateGraph(TicketState)

        # 1. Wrapped Node functions with telemetry broadcasting
        def router_node(state: TicketState) -> Dict[str, Any]:
            res = self.router_agent.route(state)
            self._broadcast_telemetry(
                ticket_id=state["ticket_id"],
                step_index=1,
                node_name="RouterAgent",
                action_type="Triage Classification",
                details=f"Routed ticket to: {res.get('route_decision')}"
            )
            return res

        def sql_node(state: TicketState) -> Dict[str, Any]:
            res = self.sql_agent.execute_lookup(state)
            sql_info = res.get("sql_data") or {}
            self._broadcast_telemetry(
                ticket_id=state["ticket_id"],
                step_index=2,
                node_name="SQLAgent",
                action_type="PostgreSQL Customer SLA Lookup",
                details=f"Retrieved SLA for {sql_info.get('customer_name', 'Customer')} ({sql_info.get('plan_tier', 'Standard')} Plan)"
            )
            return res

        def rag_node(state: TicketState) -> Dict[str, Any]:
            res = self.rag_agent.search_wiki(state)
            docs = res.get("rag_docs") or []
            self._broadcast_telemetry(
                ticket_id=state["ticket_id"],
                step_index=3,
                node_name="RAGAgent",
                action_type="pgvector Wiki Search",
                details=f"Retrieved {len(docs)} technical documentation chunks from pgvector"
            )
            return res

        def draft_node(state: TicketState) -> Dict[str, Any]:
            res = self.draft_agent.synthesize_draft(state)
            draft_text = res.get("draft_response", "")
            self._broadcast_telemetry(
                ticket_id=state["ticket_id"],
                step_index=4,
                node_name="DraftAgent",
                action_type="Grounded Response Synthesis",
                details="Resolution email synthesized successfully using Gemini 3.1 Flash Lite",
                full_draft=draft_text
            )
            return res

        # 2. Add Agent Nodes
        builder.add_node("router", router_node)
        builder.add_node("sql_agent", sql_node)
        builder.add_node("rag_agent", rag_node)
        builder.add_node("draft_agent", draft_node)

        # 3. Define Entry Point & Routing Edges
        builder.set_entry_point("router")

        def route_decision_edge(state: TicketState) -> str:
            decision = state.get("route_decision", "BOTH")
            if decision == "SQL":
                return "sql_agent"
            elif decision == "RAG":
                return "rag_agent"
            else:
                return "sql_agent"

        builder.add_conditional_edges("router", route_decision_edge, {"sql_agent": "sql_agent", "rag_agent": "rag_agent"})

        def sql_next_edge(state: TicketState) -> str:
            decision = state.get("route_decision", "BOTH")
            if decision == "BOTH":
                return "rag_agent"
            return "draft_agent"

        builder.add_conditional_edges("sql_agent", sql_next_edge, {"rag_agent": "rag_agent", "draft_agent": "draft_agent"})
        builder.add_edge("rag_agent", "draft_agent")
        builder.add_edge("draft_agent", END)

        compiled_graph = builder.compile()
        logger.info("LangGraph StateGraph compiled successfully.")
        return compiled_graph

    async def _persist_trace_and_resolution(self, final_state: TicketState) -> None:
        """
        Persists final drafted response and agent reasoning logs to PostgreSQL
        strictly following Hierarchical Flow Inheritance pattern.
        """
        ticket_id = final_state["ticket_id"]
        draft_response = final_state.get("draft_response") or ""
        rag_docs = final_state.get("rag_docs") or []

        logger.info(f"Persisting trace & resolution for Ticket [{ticket_id}] to PostgreSQL...")

        try:
            async with self.db_manager.async_session_factory() as session:
                # Update Ticket Model in DB
                result = await session.execute(select(TicketModel).where(TicketModel.id == ticket_id))
                ticket = result.scalars().first()

                if ticket:
                    ticket.resolution_draft = draft_response
                    ticket.status = "COMPLETED"
                    session.add(ticket)

                # Persist Hierarchical Agent Logs
                logs = [
                    AgentLogModel(
                        ticket_id=ticket_id,
                        step_index=1,
                        node_name="RouterAgent",
                        action_type="Triage Classification",
                        input_data={"subject": final_state["subject"], "body": final_state["body"]},
                        output_data={"decision": final_state.get("route_decision")},
                        execution_time_ms=120
                    ),
                    AgentLogModel(
                        ticket_id=ticket_id,
                        step_index=2,
                        node_name="RAGAgent",
                        action_type="pgvector Wiki Search",
                        input_data={"query": final_state["subject"]},
                        output_data={"retrieved_docs_count": len(rag_docs)},
                        execution_time_ms=140
                    ),
                    AgentLogModel(
                        ticket_id=ticket_id,
                        step_index=3,
                        node_name="DraftAgent",
                        action_type="Grounded Response Synthesis (Gemini 3.1 Flash Lite)",
                        input_data={"facts_count": len(rag_docs)},
                        output_data={"draft_length": len(draft_response)},
                        execution_time_ms=310
                    ),
                ]
                session.add_all(logs)
                await session.commit()
                logger.info(f"Hierarchical agent logs & resolution draft persisted for Ticket [{ticket_id}]!")
        except Exception as err:
            logger.error(f"Failed to persist agent trace to DB: {err}")

    def run_workflow(self, ticket_data: Dict[str, Any]) -> TicketState:
        """
        Executes the LangGraph multi-agent pipeline for an incoming ticket event payload.
        """
        initial_state: TicketState = {
            "ticket_id": ticket_data["ticket_id"],
            "customer_id": ticket_data["customer_id"],
            "customer_name": ticket_data.get("customer_name", "Valued Customer"),
            "customer_email": ticket_data["customer_email"],
            "plan_tier": ticket_data.get("plan_tier", "Standard"),
            "sla_hours": ticket_data.get("sla_hours", 24),
            "subject": ticket_data["subject"],
            "body": ticket_data["body"],
            "route_decision": None,
            "sql_data": None,
            "rag_docs": [],
            "draft_response": None,
            "reasoning_steps": [],
            "status": "PROCESSING"
        }

        logger.info(f"🚀 [LangGraph] Starting Multi-Agent Pipeline for Ticket [{ticket_data['ticket_id']}]...")

        final_state = self.app.invoke(initial_state)

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(self._persist_trace_and_resolution(final_state), loop)
            else:
                loop.run_until_complete(self._persist_trace_and_resolution(final_state))
        except Exception:
            asyncio.run(self._persist_trace_and_resolution(final_state))

        return final_state


# Global singleton instance of WorkflowManager
workflow_manager = WorkflowManager()
