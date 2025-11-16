# Implicit Decisions

- **Authentication mechanism**: Adopted stateless JWT bearer tokens signed with a symmetric secret to keep the stack dependency-light while supporting session semantics.
- **Password strategy**: Persona users are seeded with a shared configurable password (`PERSONA_SEED_PASSWORD`) to avoid embedding credentials in source control; PBKDF2-HMAC hashing keeps stored secrets opaque without external dependencies.
- **Database for tests**: Automated tests run against SQLite via SQLAlchemy to avoid managing a Postgres instance during CI while still exercising real DB interactions.
- **Frontend integration tests**: Vitest suite boots the FastAPI server with Poetry so UI tests can interact with the real API instead of mocks, trading longer test time for higher fidelity.
- **API base URL default**: Defaulted `VITE_API_BASE_URL` to `http://localhost:8000`, assuming backend runs separately; override via `.env` when deploying behind a proxy.
