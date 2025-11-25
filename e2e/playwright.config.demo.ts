import { defineConfig, devices } from "@playwright/test";

/**
 * Demo configuration for Playwright tests
 * - Headed mode (visible browser)
 * - Video recording enabled
 * - Slow motion for human-paced interactions
 * - Single worker to prevent race conditions
 */

// Read frontend port from environment (set by make demo) or default to 5173
const frontendPort = process.env.FRONTEND_PORT || "5173";

export default defineConfig({
  testDir: "./demos",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1, // Single worker for sequential demo execution
  reporter: "html",
  timeout: 10 * 60 * 1000, // 10 minutes for complete demo

  use: {
    baseURL: `http://localhost:${frontendPort}`,
    trace: "on",
    video: "on", // Always record video
    screenshot: "on",
    headless: false, // Headed mode for demo
  },

  projects: [
    {
      name: "chromium-demo",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1728, height: 972 },
      },
    },
  ],

  webServer: {
    command: "cd ../frontend && pnpm dev",
    url: `http://localhost:${frontendPort}`,
    reuseExistingServer: true,
    timeout: 120 * 1000,
  },
});
