# ⚡ Autonomous Customer Success (CS) Command Center

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-purple.svg)](https://www.langchain.com/langgraph)
[![React 18](https://img.shields.io/badge/React-18-cyan.svg)](https://react.dev/)
[![Kafka](https://img.shields.io/badge/Apache%20Kafka-7.5-black.svg)](https://kafka.apache.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-blue.svg)](https://github.com/pgvector/pgvector)

An enterprise-grade, event-driven multi-agent AI customer support automation system with real-time WebSocket telemetry, Text-to-SQL grounding, Vector RAG documentation search, and a modern monochrome React dashboard built with Feature-Sliced Design (FSD) architecture.

---

## 📐 System Architecture

```
                               ┌────────────────────────────────┐
                               │   React FSD Admin Dashboard    │
                               │    (http://localhost:3000)     │
                               └───────────────┬────────────────┘
                                               │ HTTP 202 / WebSocket
                                               ▼
                               ┌────────────────────────────────┐
                               │    FastAPI Server Gateway      │
                               │      (http://localhost:8000)   │
                               └───────────────┬────────────────┘
                                               │ Event Producer
                                               ▼
                               ┌────────────────────────────────┐
                               │       Apache Kafka Broker      │
                               │    (Topic: ticket.incoming)    │
                               └───────────────┬────────────────┘
                                               │ Consumer Poll
                                               ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                          LangGraph Multi-Agent Engine (Worker)                         │
│                                                                                        │
│   ┌──────────────┐     route     ┌──────────────┐    SLA Lookup   ┌────────────────┐   │
│   │ RouterAgent  ├──────────────►│   SQLAgent   ├────────────────►│   PostgreSQL   │   │
│   │ (Gemini 3.1) │               └──────┬───────┘                 │  (SLA & Plans) │   │
│   └──────┬───────┘                      │                         └────────────────┘   │
│          │                              ▼                                              │
│          │             RAG       ┌──────────────┐   Vector Search ┌────────────────┐   │
│          └──────────────────────►│   RAGAgent   ├────────────────►│    pgvector    │   │
│                                  └──────┬───────┘                 │ (Tech Docs DB) │   │
│                                         │                         └────────────────┘   │
│                                         ▼                                              │
│                                  ┌──────────────┐   Synthesize    ┌────────────────┐   │
│                                  │  DraftAgent  ├────────────────►│ Resolution Log │   │
│                                  │ (Gemini 3.1) │                 │  & Telemetry   │   │
│                                  └──────────────┘                 └────────────────┘   │
└─────────────────────────────────────────┬──────────────────────────────────────────────┘
                                          │ Redis Pub/Sub Stream
                                          ▼
                               ┌────────────────────────────────┐
                               │      FastAPI WebSocket Stream  │
                               │   (ws://localhost:8000/ws/...)  │
                               └────────────────────────────────┘
```

---

## 🚀 Key Features

* **Sub-50ms HTTP 202 Ingestion**: Decouples long-running LLM workflows using Apache Kafka message queue.
* **LangGraph Multi-Agent Pipeline**: Cyclic state machine routing between `RouterAgent`, `SQLAgent`, `RAGAgent`, and `DraftAgent`.
* **Grounded AI Synthesis (Gemini 3.1 Flash Lite)**: Text-to-SQL account grounding + `pgvector` technical documentation retrieval eliminates hallucinations.
* **Hierarchical Trace Audit Logs**: Persists every agent decision, tool execution time, and confidence score back to PostgreSQL `agent_logs`.
* **Real-Time Telemetry Stream**: Redis Pub/Sub bridges worker events to WebSockets for live UI timeline updates.
* **Feature-Sliced Design (FSD) React UI**: Monochromatic, minimal admin workspace (`app`, `pages`, `widgets`, `features`, `entities`, `shared`).
* **Kubernetes Production Ready**: Multi-stage Dockerfiles & K8s deployment manifests (`/k8s`).

---

## 🛠️ Tech Stack

* **Backend**: Python 3.11, FastAPI, SQLAlchemy, AsyncPG, Confluent-Kafka, Redis, LangChain, LangGraph, Google Gemini API
* **Database**: PostgreSQL 16 + `pgvector`
* **Frontend**: React 18, Vite 5, Lucide React, CSS Custom Properties (FSD Architecture)
* **DevOps**: Docker, Docker Compose, Nginx, Kubernetes (Deployments, Services, Ingress)

---

## 📦 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/autonomous-cs-command-center.git
cd autonomous-cs-command-center
```

### 2. Start Infrastructure via Docker Compose
```bash
docker compose up -d
```
*(Starts PostgreSQL on port `5433`, Kafka on `9092`, Zookeeper on `2181`, Redis on `6379`)*

### 3. Configure Gemini API Key
Edit `backend/lib/config.properties`:
```ini
[AI]
provider = gemini
llm_model = gemini-3.1-flash-lite
embedding_model = gemini-embedding-001
google_api_key = YOUR_ACTUAL_GEMINI_API_KEY
```

### 4. Setup Python Virtual Environment & Dependencies
```bash
cd backend
python -m venv .venv
# On Windows:
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 5. Launch Backend Server & Kafka Worker
**Terminal 1 (FastAPI Server)**:
```bash
uvicorn main:app --reload --port 8000
```

**Terminal 2 (Kafka Multi-Agent Worker)**:
```bash
python workers/kafka_worker.py
```

### 6. Launch Frontend React Dashboard
**Terminal 3 (Frontend)**:
```bash
cd frontend
npm install
npm run dev
```

Open **`http://localhost:3000`** in your browser!

---

## 📄 License
Distributed under the MIT License. See `LICENSE` for more information.
