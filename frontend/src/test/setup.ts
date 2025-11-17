import "@testing-library/jest-dom/vitest";

import { existsSync } from "node:fs";
import { afterAll, beforeAll } from "vitest";
import { spawn } from "node:child_process";
import path from "node:path";
import fs from "node:fs/promises";
import { request } from "node:http";

const localStorageImpl = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value;
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
    get length() {
      return Object.keys(store).length;
    },
    key: (index: number) => Object.keys(store)[index] || null,
  };
})();

Object.defineProperty(globalThis, "localStorage", {
  value: localStorageImpl,
  configurable: true,
  writable: true,
});

if (typeof window !== "undefined") {
  Object.defineProperty(window, "localStorage", {
    value: localStorageImpl,
    configurable: true,
    writable: true,
  });
}

const TEST_PORT = 8077;
const HEALTH_ENDPOINT = `http://127.0.0.1:${TEST_PORT}/healthz`;
let serverProcess: ReturnType<typeof spawn> | null = null;
let databasePath: string | null = null;

function findUvicorn(): { command: string; args: string[] } {
  const rootVenvUvicorn = path.resolve(__dirname, "../../../.venv/bin/uvicorn");
  if (existsSync(rootVenvUvicorn)) {
    return {
      command: rootVenvUvicorn,
      args: [
        "app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        String(TEST_PORT),
      ],
    };
  }
  return {
    command: "poetry",
    args: [
      "run",
      "uvicorn",
      "app.main:app",
      "--host",
      "127.0.0.1",
      "--port",
      String(TEST_PORT),
    ],
  };
}

async function waitForHealthcheck(retries = 50, delayMs = 300): Promise<void> {
  for (let attempt = 0; attempt < retries; attempt += 1) {
    try {
      const result = await new Promise<boolean>((resolve) => {
        const req = request(HEALTH_ENDPOINT, { method: "GET" }, (res) => {
          resolve(res.statusCode === 200);
        });
        req.on("error", () => resolve(false));
        req.end();
      });
      if (result) {
        return;
      }
    } catch {
      // swallow and retry
    }
    await new Promise((resolve) => setTimeout(resolve, delayMs));
  }
  throw new Error("Backend healthcheck did not succeed in time");
}

beforeAll(async () => {
  process.env.VITE_API_BASE_URL = `http://127.0.0.1:${TEST_PORT}`;
  (globalThis as { __API_BASE_URL__?: string }).__API_BASE_URL__ =
    `http://127.0.0.1:${TEST_PORT}`;

  const backendDir = path.resolve(__dirname, "../../../backend");
  const { command, args } = findUvicorn();
  databasePath = path.join(backendDir, "frontend-test.db");
  await fs.rm(databasePath, { force: true });

  serverProcess = spawn(command, args, {
    cwd: backendDir,
    env: {
      ...process.env,
      DATABASE_URL: `sqlite+aiosqlite:///${databasePath}`,
      JWT_SECRET_KEY: "frontend-test-secret",
      PERSONA_SEED_PASSWORD: "test-password",
    },
    stdio: ["ignore", "inherit", "inherit"],
    detached: false,
  });

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
