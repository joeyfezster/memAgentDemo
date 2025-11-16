# Development Plan for User Management & AI Chat Integration

## Objectives
- Enable authenticated sessions backed by the existing FastAPI/PostgreSQL stack.
- Surface predefined personas from `/docs/product/personas` as seed users.
- Extend the React frontend to support login flow and a simple AI chat placeholder.
- Deliver end-to-end functional coverage with real integration tests (no mocks).

## Plan & Success Criteria

1. **Assess existing scaffolding**
   - *Success criteria*: Document understanding of current backend/frontend capabilities and identify extension points.
2. **Design user management data model and API**
   - *Success criteria*: Schema diagram or description recorded; chosen auth mechanism justified; aligns with minimal new dependencies.

### Data Model Snapshot
- **User**: `id` (UUID), `email` (unique), `display_name`, `persona_handle`, `role`, `hashed_password`, `created_at`, `updated_at`.
- **Session / Token**: Stateless JWT signed with symmetric secret; payload includes `sub` (user id) and `exp`.
- Personas from `/docs/product/personas` mapped to seed users with deterministic password `changeme` hashed via bcrypt (configurable via env later).
3. **Implement backend user management**
   - *Success criteria*: User model, CRUD, authentication endpoints; seed personas available; tests cover login + persona retrieval using real DB interactions.
4. **Integrate frontend authentication flow**
   - *Success criteria*: Login form connects to backend; authenticated state preserved (e.g., via context/local storage); UI shows logged-in user data.
5. **Add AI chat placeholder tied to session**
   - *Success criteria*: Authenticated users can send a message and receive `"hi <user name>"` response.
6. **End-to-end functional tests**
   - *Success criteria*: Backend and frontend test suites exercise new functionality without mocks; all tests pass.
7. **Documentation & implicit decisions**
   - *Success criteria*: Implicit decisions captured in dedicated markdown; README(s) updated if workflow changes; plan/todo reflects completion.

## TODO Tracker

| Task | Status | Notes |
| --- | --- | --- |
| Review scaffolding | Done | Backend FastAPI + async SQLAlchemy; Frontend React login placeholder |
| Finalize data model/auth approach | Done | Personas mapped to seeded `user` table with JWT bearer tokens |
| Implement backend changes | Done | Models, auth endpoints, persona seeding |
| Implement frontend changes | Done | Login wiring, chat workspace UI |
| Add functional tests | Done | Backend + frontend exercising real API |
| Update docs & decisions | Done | README updates and implicit decisions recorded |
| Run test suites | Done | `make test USE_DOCKER=0` successful |
