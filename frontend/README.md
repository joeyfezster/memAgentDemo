# Frontend

React + Vite + TypeScript application for the memAgent demo platform.

## Getting started

```bash
pnpm install
pnpm dev
```

Set `VITE_API_BASE_URL` (see `.env.example`) so the UI can reach the FastAPI backend.

### Agent explorer demo data

Set `VITE_AGENT_EXPLORER_SAMPLE=true` when running `pnpm dev` to show the
agent/memory explorer with built-in sample data. When the flag is omitted the UI
calls the `/letta/agents/*` endpoints and renders live data from your Letta
server.

## Testing

```bash
pnpm test
```

The Vitest suite launches the FastAPI server with an ephemeral SQLite database and
exercises the authentication + chat workflow end-to-end.
