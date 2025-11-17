# Work Plan

## TODO
- [x] Review product tool mockups and personas to understand required capabilities.
- [x] Design a shared mock data repository to drive tool responses.
- [x] Implement letta tool classes for each mockup under `backend/agent/tools`.
- [x] Provide helper utilities (geo filtering, scoring) needed by the tools.
- [x] Write focused unit tests covering every tool's behavior.
- [x] Extend the letta integration test so an agent exercises multiple tools.
- [x] Run the backend test suite and document results.

## Decisions & Notes
- Tools share a single in-memory dataset (`MockDataRepository`) to keep behavior deterministic.
- Each tool class avoids referencing `self` inside `run` to remain Letta-compliant.
