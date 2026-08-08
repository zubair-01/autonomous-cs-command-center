from typing import Any, Dict, List, Optional, TypedDict


class TicketState(TypedDict):
    """
    LangGraph Shared State Dictionary for Multi-Agent Support Ticket Pipeline.
    Passed between RouterAgent, SQLAgent, RAGAgent, and DraftAgent nodes.
    """
    ticket_id: str
    customer_id: str
    customer_name: str
    customer_email: str
    plan_tier: str
    sla_hours: int
    subject: str
    body: str
    route_decision: Optional[str]  # "SQL", "RAG", or "BOTH"
    sql_data: Optional[Dict[str, Any]]
    rag_docs: Optional[List[Dict[str, Any]]]
    draft_response: Optional[str]
    reasoning_steps: List[Dict[str, Any]]
    status: str  # "PROCESSING", "DRAFTED", "FAILED"
