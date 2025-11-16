# Frontend

React + Vite + TypeScript application for the memAgent demo platform.

## Getting started

```bash
pnpm install
pnpm dev
```

Set `VITE_API_BASE_URL` (see `.env.example`) so the UI can reach the FastAPI backend.

## Testing

```bash
pnpm test
```

The Vitest suite launches the FastAPI server with an ephemeral SQLite database and
exercises the authentication + chat workflow end-to-end.
