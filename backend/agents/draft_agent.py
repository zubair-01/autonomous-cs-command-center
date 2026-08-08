from typing import Any, Dict
from agents.state import TicketState
from langchain_core.messages import SystemMessage, HumanMessage
from lib.config_loader import config_loader
from utils.log import logger

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


class DraftAgent:
    """
    OOP Draft Agent responsible for synthesizing final email responses to customers
    strictly grounded in facts retrieved by the SQLAgent (SLA/billing) and RAGAgent (technical wiki).
    """

    def __init__(self):
        self.api_key = config_loader.get("AI", "google_api_key", "")
        self.model_name = config_loader.get("AI", "llm_model", "gemini-3.1-flash-lite")
        self.llm = self._init_llm()

    def _init_llm(self):
        """Initializes the Gemini LLM client if API key is configured."""
        if HAS_GEMINI and self.api_key and "YOUR_" not in self.api_key:
            try:
                logger.info(f"Initializing DraftAgent with Gemini model [{self.model_name}]...")
                return ChatGoogleGenerativeAI(
                    model=self.model_name,
                    google_api_key=self.api_key,
                    temperature=0.2
                )
            except Exception as e:
                logger.warning(f"Could not initialize ChatGoogleGenerativeAI for DraftAgent: {e}")
                return None
        return None

    def synthesize_draft(self, state: TicketState) -> Dict[str, Any]:
        """
        Synthesizes a grounded customer support resolution email.
        """
        ticket_id = state["ticket_id"]
        customer_name = state.get("customer_name", "Valued Customer")
        plan_tier = state.get("plan_tier", "Standard")
        sla_hours = state.get("sla_hours", 24)
        subject = state["subject"]
        body = state["body"]

        sql_data = state.get("sql_data") or {}
        rag_docs = state.get("rag_docs") or []

        logger.info(f"[DraftAgent] Synthesizing grounded resolution draft for Ticket [{ticket_id}] using [{self.model_name}]...")

        # 1. Try Gemini LLM generation if configured
        if self.llm:
            try:
                system_prompt = (
                    "You are a Senior Customer Success Engineer writing an official resolution email to a SaaS customer. "
                    "Synthesize a clear, empathetic, technical response grounded strictly in the provided Database facts and Documentation context.\n"
                    "Do NOT invent facts. Acknowledge their plan tier and SLA guarantee.\n"
                    "Format cleanly with professional email greeting and signature."
                )
                context_str = (
                    f"Customer: {customer_name}\n"
                    f"Plan Tier: {plan_tier} (Guaranteed SLA: {sla_hours} hours)\n"
                    f"Issue Subject: {subject}\n"
                    f"Issue Body: {body}\n\n"
                    f"Database Facts (SQL): {sql_data}\n"
                    f"Technical Wiki Context (RAG): {rag_docs}\n"
                )
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=context_str)
                ]
                response = self.llm.invoke(messages)
                draft_text = response.content.strip()

                logger.info(f"[DraftAgent] Gemini [{self.model_name}] generated resolution draft successfully.")
                return {
                    "draft_response": draft_text,
                    "status": "DRAFTED"
                }
            except Exception as err:
                logger.warning(f"[DraftAgent] Gemini invocation failed, falling back to template synthesis: {err}")

        # 2. Production fallback template synthesis
        doc_highlights = "\n".join([f"- {d['title']}: {d['content']}" for d in rag_docs]) if rag_docs else "- Inspected database configuration parameters."

        account_status = sql_data.get("account_status", "ACTIVE") if isinstance(sql_data, dict) else "ACTIVE"

        fallback_draft = (
            f"Dear {customer_name},\n\n"
            f"Thank you for contacting Support regarding: '{subject}'.\n\n"
            f"As an esteemed {plan_tier} Plan customer (Guaranteed SLA: {sla_hours} hours), your ticket has been "
            f"prioritized by our Autonomous AI Engineering pipeline.\n\n"
            f"### Technical Resolution & Diagnosis:\n"
            f"{doc_highlights}\n\n"
            f"### Action Plan:\n"
            f"Our engineering team has verified your account configuration ({account_status}). "
            f"If you continue to experience intermittent gateway timeouts, please ensure your connection pool settings match "
            f"the parameters outlined in our documentation.\n\n"
            f"Best regards,\n"
            f"Customer Success Engineering Team\n"
            f"Autonomous CS Command Center"
        )

        logger.info(f"[DraftAgent] Template synthesis generated draft successfully.")
        return {
            "draft_response": fallback_draft,
            "status": "DRAFTED"
        }
