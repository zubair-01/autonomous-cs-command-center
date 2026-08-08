import asyncio
from typing import Any, Dict, List
from agents.state import TicketState
from db.database_manager import db_manager
from models.schemas import DocEmbeddingModel
from sqlalchemy.future import select
from utils.log import logger


class RAGAgent:
    """
    OOP Vector RAG Agent responsible for searching pgvector documentation wiki
    to retrieve relevant technical troubleshooting articles.
    """

    def __init__(self):
        self.db_manager = db_manager

    async def search_wiki_async(self, state: TicketState) -> Dict[str, Any]:
        """
        Asynchronously searches pgvector table for relevant technical documentation.
        """
        subject = state["subject"]
        body = state["body"]
        search_text = f"{subject} {body}".lower()
        logger.info(f"[RAGAgent] Searching pgvector technical wiki for query: {subject}")

        retrieved_docs: List[Dict[str, Any]] = []

        try:
            async with self.db_manager.async_session_factory() as session:
                # Query all seeded doc embeddings
                result = await session.execute(select(DocEmbeddingModel))
                docs = result.scalars().all()

                for doc in docs:
                    title_lower = doc.title.lower()
                    content_lower = doc.content.lower()

                    # Simple keyword relevance score (enhanced vector search operator <=> used when OpenAI/Gemini embeddings generated)
                    relevance = 0.0
                    if any(w in title_lower for w in search_text.split()):
                        relevance += 0.5
                    if any(w in content_lower for w in search_text.split()):
                        relevance += 0.3

                    if relevance > 0.0 or len(docs) <= 3:
                        retrieved_docs.append({
                            "doc_id": doc.id,
                            "title": doc.title,
                            "category": doc.category,
                            "content": doc.content,
                            "relevance_score": round(relevance, 2)
                        })

                # Sort by relevance score
                retrieved_docs.sort(key=lambda x: x["relevance_score"], reverse=True)
                logger.info(f"[RAGAgent] Retrieved {len(retrieved_docs)} technical wiki articles from pgvector.")
        except Exception as e:
            logger.warning(f"[RAGAgent] Database wiki search warning: {e}")

        # Fallback doc if no docs matched
        if not retrieved_docs:
            retrieved_docs.append({
                "doc_id": "default-001",
                "title": "General Infrastructure Troubleshooting Guide",
                "category": "General",
                "content": "Verify system configuration parameters in backend/lib/config.properties and inspect log/app.log for exception tracebacks.",
                "relevance_score": 0.5
            })

        return {"rag_docs": retrieved_docs[:2]}

    def search_wiki(self, state: TicketState) -> Dict[str, Any]:
        """Synchronous wrapper for LangGraph node execution."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return asyncio.run_coroutine_threadsafe(self.search_wiki_async(state), loop).result()
            else:
                return loop.run_until_complete(self.search_wiki_async(state))
        except Exception:
            return asyncio.run(self.search_wiki_async(state))
