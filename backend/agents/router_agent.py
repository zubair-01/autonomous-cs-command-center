import json
from typing import Dict
from agents.state import TicketState
from langchain_core.messages import SystemMessage, HumanMessage
from lib.config_loader import config_loader
from utils.log import logger

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


class RouterAgent:
    """
    OOP Router Agent responsible for evaluating incoming customer support tickets
    and determining whether the workflow should route to:
    - 'SQL': Customer SLA / Billing / Plan lookup
    - 'RAG': Technical Documentation search
    - 'BOTH': Both SQL lookup and RAG search
    """

    def __init__(self):
        self.api_key = config_loader.get("AI", "google_api_key", "")
        self.model_name = config_loader.get("AI", "llm_model", "gemini-3.1-flash-lite")
        self.llm = self._init_llm()

    def _init_llm(self):
        """Initializes the Gemini LLM client if API key is configured."""
        if HAS_GEMINI and self.api_key and "YOUR_" not in self.api_key:
            try:
                logger.info(f"Initializing RouterAgent with Gemini model [{self.model_name}]...")
                return ChatGoogleGenerativeAI(
                    model=self.model_name,
                    google_api_key=self.api_key,
                    temperature=0.0
                )
            except Exception as e:
                logger.warning(f"Could not initialize ChatGoogleGenerativeAI for RouterAgent: {e}")
                return None
        return None

    def route(self, state: TicketState) -> Dict[str, str]:
        """
        Analyzes state and returns routing decision ('SQL', 'RAG', or 'BOTH').
        """
        logger.info(f"[RouterAgent] Analyzing ticket subject: {state['subject']}")

        subject_lower = state["subject"].lower()
        body_lower = state["body"].lower()
        combined_text = f"{subject_lower} {body_lower}"

        # 1. Try Gemini LLM classification if initialized
        if self.llm:
            try:
                system_prompt = (
                    "You are an expert AI Triage Router for Customer Support. "
                    "Analyze the support issue and output JSON with a single key 'decision' "
                    "which must be exactly one of: 'SQL', 'RAG', or 'BOTH'.\n"
                    "- Choose 'SQL' for billing, SLA, account upgrades, or plan limit questions.\n"
                    "- Choose 'RAG' for technical errors, 504 timeouts, webhooks, or API documentation.\n"
                    "- Choose 'BOTH' if the issue involves both account limits/SLA AND technical troubleshooting."
                )
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=f"Subject: {state['subject']}\nBody: {state['body']}")
                ]
                response = self.llm.invoke(messages)
                content = response.content.strip()

                if "SQL" in content.upper() and "RAG" in content.upper():
                    decision = "BOTH"
                elif "SQL" in content.upper():
                    decision = "SQL"
                elif "RAG" in content.upper():
                    decision = "RAG"
                else:
                    decision = "BOTH"

                logger.info(f"[RouterAgent] Gemini model [{self.model_name}] decided route: {decision}")
                return {"route_decision": decision}
            except Exception as err:
                logger.warning(f"[RouterAgent] Gemini invocation failed, falling back to rule engine: {err}")

        # 2. Rule-based fallback triage engine
        is_sql = any(k in combined_text for k in ["billing", "sla", "plan", "upgrade", "charge", "invoice", "limit", "account"])
        is_rag = any(k in combined_text for k in ["error", "timeout", "504", "500", "database", "api", "webhook", "bug", "crash", "postgresql"])

        if is_sql and is_rag:
            decision = "BOTH"
        elif is_sql:
            decision = "SQL"
        else:
            decision = "RAG"

        logger.info(f"[RouterAgent] Rule engine decided route: {decision}")
        return {"route_decision": decision}
