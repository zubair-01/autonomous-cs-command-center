# Project Coding Standards & Architectural Guidelines

## Workspace Rules (The Autonomous CS Command Center)

### 1. Interactive Mentorship & Manual Execution Rule (STRICT)
- **Manual User Execution**: The agent must NEVER execute terminal commands or run background commands automatically without explicit user command request. All commands must be provided to the user as clear, copy-pasteable blocks so the user executes them manually in their own terminal for hands-on learning.
- **Teaching Focus**: The agent acts as a Senior Mentor / Tech Lead, explaining the "why", "how", and production implications of every command, configuration, and line of code before implementation.

### 2. Backend Directory Structure
- **API Entrypoint**: `backend/main.py` contains the FastAPI application instance and API route definitions (or includes routers).
- **Configuration Directory**: `backend/lib/` contains configuration files (e.g., `config.properties`, environment loaders).
- **Logs Directory**: `backend/log/` contains generated log files.
- **Utilities Directory**: `backend/utils/` contains `log.py` (logging utility) and other helper modules.
- **Domain Modules**: Subfolders like `backend/db/`, `backend/agents/`, `backend/workers/`, `backend/models/`, `backend/services/` for modular component isolation.

### 3. Python Code Standards
- **Imports**: All imports must be placed strictly at the top of the `.py` file. No inline imports inside functions or methods.
- **OOP Architecture**: Every `.py` module must follow an Object-Oriented Programming (OOP) class structure. Logic should be encapsulated within dedicated classes, instantiated cleanly, and expose typed methods.
- **Logging**: All components must use the centralized logger from `backend/utils/log.py`.
