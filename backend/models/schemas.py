import datetime
import uuid
from typing import Any, Dict, Optional
from pgvector.sqlalchemy import Vector
from pydantic import BaseModel, Field
from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# =============================================================================
# SQLAlchemy ORM Models (Data Layer with Hierarchical Flow Inheritance)
# =============================================================================

class CustomerModel(Base):
    """
    SQLAlchemy ORM model for Customer Accounts.
    """
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    plan_tier = Column(String(50), nullable=False, default="Standard")  # Standard, Pro, Enterprise
    sla_hours = Column(Integer, nullable=False, default=24)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    tickets = relationship("TicketModel", back_populates="customer", cascade="all, delete-orphan")


class TicketModel(Base):
    """
    SQLAlchemy ORM model for Customer Support Tickets.
    """
    __tablename__ = "tickets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="PENDING")  # PENDING, PROCESSING, COMPLETED, REJECTED
    resolution_draft = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    customer = relationship("CustomerModel", back_populates="tickets")
    agent_logs = relationship("AgentLogModel", back_populates="ticket", cascade="all, delete-orphan", order_by="AgentLogModel.step_index")


class AgentLogModel(Base):
    """
    SQLAlchemy ORM model for Agent Execution Logs (Hierarchical Flow Inheritance).
    Maps multi-agent reasoning steps directly back to the parent Ticket.
    """
    __tablename__ = "agent_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_id = Column(String(36), ForeignKey("tickets.id"), nullable=False)
    step_index = Column(Integer, nullable=False)
    node_name = Column(String(50), nullable=False)  # Router, SQLAgent, RAGAgent, DraftAgent
    action_type = Column(String(100), nullable=False)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    execution_time_ms = Column(Integer, nullable=False, default=0)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    ticket = relationship("TicketModel", back_populates="agent_logs")


class DocEmbeddingModel(Base):
    """
    SQLAlchemy ORM model for Vector RAG Documentation Wiki (pgvector).
    Stores technical article chunks with 1536-dimensional vector embeddings.
    """
    __tablename__ = "doc_embeddings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


# =============================================================================
# Pydantic Schemas (API Request/Response Data Validation)
# =============================================================================

class TicketCreateSchema(BaseModel):
    """Payload for submitting a new support ticket."""
    customer_email: str = Field(..., example="alice@acme.com")
    subject: str = Field(..., example="Database connection error in Enterprise API")
    body: str = Field(..., example="We are experiencing intermittent 504 gateway timeouts when connecting to PostgreSQL.")


class TicketResponseSchema(BaseModel):
    """API response schema for ticket confirmation."""
    ticket_id: str
    status: str
    message: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class AgentLogSchema(BaseModel):
    """Telemetry schema for agent step updates broadcast via WebSockets."""
    ticket_id: str
    step_index: int
    node_name: str
    action_type: str
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    execution_time_ms: int
    timestamp: datetime.datetime

    class Config:
        from_attributes = True
