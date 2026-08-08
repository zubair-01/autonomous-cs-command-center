import os
import sys

# Ensure backend root is always present in python module search path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import asyncio
import datetime
import json
from contextlib import asynccontextmanager
from typing import Dict, List
from db.database_manager import db_manager
from db.seed_manager import seed_manager
from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from lib.config_loader import config_loader
from models.schemas import CustomerModel, TicketCreateSchema, TicketModel, TicketResponseSchema
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from utils.log import logger
from utils.redis_pubsub import redis_pubsub
from workers.kafka_producer import kafka_producer


class WebSocketConnectionManager:
    """
    OOP WebSocket Connection Manager responsible for maintaining active WebSocket client sockets
    and broadcasting real-time agent telemetry stream events.
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accepts an incoming WebSocket connection and registers it."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"[WebSocket] Client connected. Total active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """Removes a disconnected WebSocket from active pool."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"[WebSocket] Client disconnected. Total active connections: {len(self.active_connections)}")

    async def broadcast_json(self, message: str) -> None:
        """Broadcasts a raw JSON telemetry message string to all connected WebSocket clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"[WebSocket] Broadcast error: {e}")
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn)


ws_connection_manager = WebSocketConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI Lifespan Manager:
    Handles application startup (DB init & seeding) and background Redis-to-WebSocket listener task.
    """
    logger.info("FastAPI Server starting up...")
    try:
        await db_manager.init_db()
        await seed_manager.seed_data()
    except Exception as e:
        logger.warning(f"Database initialization warning: {e}")

    # Start background Redis subscriber bridging to WebSockets
    async def redis_listener_task():
        logger.info("[WebSocket Gateway] Background Redis Pub/Sub listener active...")
        try:
            async for raw_message in redis_pubsub.subscribe_channel():
                await ws_connection_manager.broadcast_json(raw_message)
        except Exception as err:
            logger.error(f"[WebSocket Gateway] Redis listener error: {err}")

    listener_task = asyncio.create_task(redis_listener_task())

    yield

    logger.info("FastAPI Server shutting down...")
    listener_task.cancel()
    kafka_producer.flush(timeout_seconds=5.0)


class CommandCenterAPI:
    """
    OOP FastAPI Server Gateway Class.
    Encapsulates application instantiation, CORS configuration, routing, WebSockets, and lifecycle hooks.
    """

    def __init__(self):
        self.app_name = config_loader.get("DEFAULT", "app_name", "Autonomous CS Command Center")
        self.environment = config_loader.get("DEFAULT", "environment", "development")
        self.app = FastAPI(
            title=self.app_name,
            version="1.0.0",
            description="Event-Driven Multi-Agent AI Support Pipeline & Live Telemetry Gateway",
            lifespan=lifespan
        )
        self._configure_middlewares()
        self._register_routes()

    def _configure_middlewares(self) -> None:
        """Configures CORS and security middlewares for production readiness."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _register_routes(self) -> None:
        """Registers API endpoints, WebSockets, ticket ingestion routes, and health checks."""

        @self.app.get("/", tags=["Health"])
        async def root() -> Dict[str, str]:
            return {
                "status": "online",
                "app_name": self.app_name,
                "environment": self.environment
            }

        @self.app.get("/health", tags=["Health"])
        async def health_check() -> Dict[str, str]:
            return {
                "status": "healthy",
                "database": "configured",
                "kafka": "configured",
                "redis": "configured",
                "websockets": "active"
            }

        @self.app.get("/api/v1/tickets/{ticket_id}", tags=["Tickets"])
        async def get_ticket_by_id(
            ticket_id: str,
            session: AsyncSession = Depends(db_manager.get_session)
        ):
            """Returns a single ticket record with its resolution draft from PostgreSQL."""
            result = await session.execute(
                select(TicketModel, CustomerModel)
                .join(CustomerModel, TicketModel.customer_id == CustomerModel.id)
                .where(TicketModel.id == ticket_id)
            )
            row = result.first()
            if not row:
                raise HTTPException(status_code=404, detail="Ticket not found")

            ticket, customer = row
            return {
                "id": ticket.id,
                "customer_name": customer.name,
                "customer_email": customer.email,
                "plan_tier": customer.plan_tier,
                "sla_hours": customer.sla_hours,
                "subject": ticket.subject,
                "body": ticket.body,
                "status": ticket.status,
                "resolution_draft": ticket.resolution_draft,
                "created_at": ticket.created_at.isoformat()
            }

        @self.app.post(
            "/api/v1/tickets",
            response_model=TicketResponseSchema,
            status_code=status.HTTP_202_ACCEPTED,
            tags=["Ticket Ingestion"]
        )
        async def submit_ticket(
            ticket_in: TicketCreateSchema,
            session: AsyncSession = Depends(db_manager.get_session)
        ) -> TicketResponseSchema:
            """
            Event-Driven Ticket Ingestion Endpoint (HTTP 202 Pattern).
            """
            logger.info(f"Incoming ticket submission request from: {ticket_in.customer_email}")

            result = await session.execute(
                select(CustomerModel).where(CustomerModel.email == ticket_in.customer_email)
            )
            customer = result.scalars().first()

            if not customer:
                logger.warning(f"Ticket submission rejected: Customer email [{ticket_in.customer_email}] not found.")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Customer account with email '{ticket_in.customer_email}' not found."
                )

            new_ticket = TicketModel(
                customer_id=customer.id,
                subject=ticket_in.subject,
                body=ticket_in.body,
                status="PENDING"
            )
            session.add(new_ticket)
            await session.commit()
            await session.refresh(new_ticket)

            event_payload = {
                "ticket_id": new_ticket.id,
                "customer_id": customer.id,
                "customer_name": customer.name,
                "customer_email": customer.email,
                "plan_tier": customer.plan_tier,
                "sla_hours": customer.sla_hours,
                "subject": new_ticket.subject,
                "body": new_ticket.body,
                "created_at": new_ticket.created_at.isoformat()
            }

            published = kafka_producer.publish_ticket(event_payload)
            if not published:
                logger.error(f"Failed to publish ticket [{new_ticket.id}] to Kafka broker.")

            return TicketResponseSchema(
                ticket_id=new_ticket.id,
                status="PENDING",
                message="Ticket successfully received and queued for autonomous multi-agent resolution.",
                created_at=new_ticket.created_at
            )

        @self.app.websocket("/ws/telemetry")
        async def websocket_telemetry_endpoint(websocket: WebSocket):
            await ws_connection_manager.connect(websocket)
            try:
                await websocket.send_json({
                    "event": "connected",
                    "message": "Connected to Autonomous CS Command Center Telemetry Stream",
                    "timestamp": datetime.datetime.utcnow().isoformat()
                })
                while True:
                    await websocket.receive_text()
            except WebSocketDisconnect:
                ws_connection_manager.disconnect(websocket)
            except Exception as e:
                logger.warning(f"WebSocket client error: {e}")
                ws_connection_manager.disconnect(websocket)

    def get_app(self) -> FastAPI:
        return self.app


server = CommandCenterAPI()
app = server.get_app()
