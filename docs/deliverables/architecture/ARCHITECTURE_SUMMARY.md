# memAgent Demo - Complete Architecture Documentation

## 📚 Documentation Suite (8 Documents)

### 1. **01-system-context.md** (Level 1 - High Level)

Strategic overview showing the system in its environment:

- System purpose and capabilities
- External dependencies (OpenAI, Letta, Placer.ai)
- User types and personas
- Key use cases
- C4 Context diagram

**Start here if**: You need to understand WHAT the system does and WHO uses it

---

### 2. **02-container-diagram.md** (Level 2 - Deployment)

Deployment architecture:

- 4 containers: Frontend (React), Backend (FastAPI), Letta (Agent Server), PostgreSQL
- Inter-container communication
- Docker Compose configuration
- Environment variables
- Health checks
- C4 Container diagram

**Start here if**: You need to deploy, run, or debug infrastructure

---

### 3. **03-backend-components.md** (Level 3 - Backend Deep Dive)

Backend internal structure:

- API layer (4 routers: health, auth, chat, letta)
- CRUD layer (database operations)
- Service layer (persona service with shared memory logic)
- Core utilities (Letta client, security, config)
- Database models and relationships
- Agent tools (8 Placer.ai tools + 2 persona tools)
- Request flow examples
- C4 Component diagram (backend)

**Start here if**: You're a backend developer or need to understand API structure

---

### 4. **04-frontend-components.md** (Level 3 - Frontend Deep Dive)

**⭐ HAS NICE SCREENSHOTS ⭐**

Frontend internal structure:

- Component hierarchy (App → Auth/Chat/AgentExplorer)
- Authentication flow
- Chat workspace (Sidebar, ChatWindow, MessageList, MessageInput)
- Agent Explorer (AgentGraph, MemoryDetail, ArchivalTable)
- API client module with type definitions
- State management patterns
- C4 Component diagram (frontend)

**Start here if**: You're a frontend developer or need to understand UI architecture

---

### 5. **05-agent-architecture.md** (Level 3 - AI Agent System)

Deep dive into the AI agent system:

- Agent lifecycle (creation, initialization, message handling, tool execution)
- Memory block types and hierarchy
- Tool ecosystem (10 tools documented in detail)
- Agent reasoning flow with multi-step query example
- LLM configuration (GPT-4o settings)
- Pi agent system prompt structure
- Data repository (mock Placer.ai implementation)
- Agent architecture diagram

**Start here if**: You need to understand how agents work, add tools, or modify agent behavior

---

### 6. **06-memory-architecture.md** (Level 3 - Memory System)

**⭐ MOST IMPORTANT DOCUMENT ⭐**

Detailed explanation of the shared memory system:

- Database schema (User, Persona, UserPersonaBridge, Conversation, Message)
- Memory block hierarchy (4 types: agent_persona, human, user_persona_profile, shared)
- Persona discovery and association flow
- Shared memory block creation (thread-safe with locking)
- Multi-user attachment mechanism
- Privacy and security guarantees
- Detailed collaboration example (Alice → Bob → Carol)
- Performance and scalability considerations
- Memory architecture diagram + sequence diagrams

**Start here if**: You need to understand the core innovation or implement persona features

---

## 🔑 Key Concepts Explained

### Persona

A professional identity combining industry + role (e.g., "qsr_real_estate"). Users are discovered and associated with personas through natural conversation.

### Shared Memory Block

A Letta memory block attached to multiple agents serving users with the same persona. Enables collective learning while preserving privacy.

### Core Memory

Small, fast memory (10-18K chars) always loaded into agent context. Includes agent identity, personal facts, and professional context.

### Archival Memory

Unlimited vector-indexed storage for conversation history. Retrieved via semantic similarity search when relevant.

### Pi Agent

The AI assistant personality - an expert in location analytics, configured via `pi_agent_base.af` with specific system prompt and tools.

---

## 🔍 Key Files Reference

| Component           | Path                                      | Purpose                     |
| ------------------- | ----------------------------------------- | --------------------------- |
| Agent Config        | `backend/app/core/pi_agent_base.af`       | Pi agent template (JSON)    |
| Letta Integration   | `backend/app/core/letta_client.py`        | Agent creation & messaging  |
| Shared Memory Logic | `backend/app/services/persona_service.py` | Block creation & attachment |
| Chat API            | `backend/app/api/chat.py`                 | Conversation endpoints      |
| Location Tools      | `backend/agent/tools/placer_tools.py`     | 8 Placer.ai-style tools     |
| Persona Tools       | `backend/agent/tools/persona_tools.py`    | Persona system tools        |
| Frontend Root       | `frontend/src/App.tsx`                    | React app root              |
| Chat UI             | `frontend/src/components/ChatWindow.tsx`  | Message interface           |
| Memory Viz          | `frontend/src/components/AgentExplorer/`  | Agent memory explorer       |
| Deployment          | `infra/docker-compose.yml`                | Container orchestration     |
