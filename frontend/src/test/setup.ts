import "@testing-library/jest-dom/vitest";

import { afterAll, beforeAll } from "vitest";
import { spawn } from "node:child_process";
import path from "node:path";
import fs from "node:fs/promises";

const TEST_PORT = 8077;
const HEALTH_ENDPOINT = `http://127.0.0.1:${TEST_PORT}/healthz`;
let serverProcess: ReturnType<typeof spawn> | null = null;
let databasePath: string | null = null;

async function waitForHealthcheck(retries = 30, delayMs = 200): Promise<void> {
  for (let attempt = 0; attempt < retries; attempt += 1) {
    try {
      const response = await fetch(HEALTH_ENDPOINT);
      if (response.ok) {
        return;
      }
    } catch (error) {
      // swallow and retry
    }
    await new Promise((resolve) => setTimeout(resolve, delayMs));
  }
  throw new Error("Backend healthcheck did not succeed in time");
}

beforeAll(async () => {
  process.env.VITE_API_BASE_URL = `http://127.0.0.1:${TEST_PORT}`;
  (globalThis as { __API_BASE_URL__?: string }).__API_BASE_URL__ = `http://127.0.0.1:${TEST_PORT}`;
  const backendDir = path.resolve(__dirname, "../../../backend");
  databasePath = path.join(backendDir, "frontend-test.db");
  await fs.rm(databasePath, { force: true });

  serverProcess = spawn(
    "poetry",
    [
      "run",
      "uvicorn",
      "app.main:app",
      "--host",
      "127.0.0.1",
      "--port",
      String(TEST_PORT),
    ],
    {
      cwd: backendDir,
      env: {
        ...process.env,
        DATABASE_URL: `sqlite+aiosqlite:///${databasePath}`,
        JWT_SECRET_KEY: "frontend-test-secret",
        PERSONA_SEED_PASSWORD: "test-password",
      },
      stdio: "inherit",
    },
  );

  serverProcess.on("exit", (code) => {
    if (code !== 0) {
      console.error(`Backend server exited with code ${code}`);
    }
  });

  await waitForHealthcheck();
});

afterAll(async () => {
  if (serverProcess) {
    serverProcess.kill("SIGTERM");
  }
  (globalThis as { __API_BASE_URL__?: string }).__API_BASE_URL__ = undefined;
  if (databasePath) {
    await fs.rm(databasePath, { force: true });
  }
});
