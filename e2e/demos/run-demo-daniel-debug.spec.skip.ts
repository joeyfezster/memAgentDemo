import { test, expect, Page } from "@playwright/test";

/**
 * DEBUG VERSION - Demo Script Runner for Daniel Persona
 * With comprehensive instrumentation to diagnose stuck issues
 */

const DEMO_EMAIL = "daniel.insights@goldtobacco.com";
const DEMO_PASSWORD = "changeme123";
const TYPING_DELAY_MIN = 25;
const TYPING_DELAY_MAX = 74;
const PAUSE_AFTER_MESSAGE = 3000;

/**
 * Log memory usage
 */
async function logMemoryUsage(page: Page, label: string) {
  try {
    const metrics = await page.evaluate(() => {
      const perf = performance as any;
      return {
        jsHeap: perf.memory?.usedJSHeapSize || 0,
        jsHeapLimit: perf.memory?.jsHeapSizeLimit || 0,
        domNodes: document.querySelectorAll("*").length,
        agentMessages: document.querySelectorAll(
          '[data-testid="message"][data-role="assistant"]',
        ).length,
        toolInteractions: document.querySelectorAll(
          ".tool-interaction__details",
        ).length,
      };
    });
    console.log(`📊 Memory at ${label}:`);
    console.log(
      `   JS Heap: ${(metrics.jsHeap / 1024 / 1024).toFixed(2)} MB / ${(
        metrics.jsHeapLimit /
        1024 /
        1024
      ).toFixed(2)} MB`,
    );
    console.log(`   DOM Nodes: ${metrics.domNodes}`);
    console.log(`   Agent Messages: ${metrics.agentMessages}`);
    console.log(`   Tool Interactions: ${metrics.toolInteractions}`);
  } catch (e) {
    console.log(`⚠️  Could not log memory: ${e}`);
  }
}

/**
 * Check for pending network requests
 */
async function checkPendingRequests(page: Page, label: string) {
  try {
    const pending = await page.evaluate(() => {
      return (performance as any)
        .getEntriesByType("resource")
        .filter((r: any) => r.responseEnd === 0)
        .map((r: any) => r.name);
    });
    if (pending.length > 0) {
      console.log(`🔄 Pending requests at ${label}: ${pending.length}`);
      pending.forEach((url: string) => console.log(`   ${url}`));
    } else {
      console.log(`✅ No pending requests at ${label}`);
    }
  } catch (e) {
    console.log(`⚠️  Could not check pending requests: ${e}`);
  }
}

/**
 * Inspect streaming attribute states
 */
async function inspectStreamingAttributes(page: Page, label: string) {
  try {
    const messages = await page
      .locator('[data-testid="message"][data-role="assistant"]')
      .all();
    console.log(
      `🔍 Streaming inspection at ${label}: Found ${messages.length} messages`,
    );

    for (let i = 0; i < messages.length; i++) {
      const msg = messages[i];
      const streamingAttr = await msg.getAttribute("data-streaming");
      const isVisible = await msg.isVisible();
      const hasClass = await msg.evaluate((el) => el.className);

      console.log(`   Message ${i}:`);
      console.log(
        `     data-streaming: "${streamingAttr}" (type: ${typeof streamingAttr})`,
      );
      console.log(`     visible: ${isVisible}`);
      console.log(`     classes: ${hasClass}`);
      console.log(
        `     matches :not([data-streaming="true"]): ${
          streamingAttr !== "true"
        }`,
      );
    }
  } catch (e) {
    console.log(`⚠️  Could not inspect streaming attributes: ${e}`);
  }
}

/**
 * Type text slowly like a human
 */
async function typeSlowly(page: Page, text: string) {
  const input = page.getByPlaceholder(/type.*message/i);
  await input.waitFor({ state: "visible", timeout: 5000 });
  await input.click();
  await page.waitForTimeout(500);

  for (const char of text) {
    await page.keyboard.type(char);
    const delay =
      Math.random() * (TYPING_DELAY_MAX - TYPING_DELAY_MIN) + TYPING_DELAY_MIN;
    await page.waitForTimeout(delay);
  }
}

/**
 * Wait for agent response with comprehensive debugging
 */
async function waitForAgentResponse(page: Page, messageLabel: string) {
  console.log(`\n🔍 [${messageLabel}] Waiting for agent response...`);

  // STEP 1: Wait for at least one agent message to appear
  console.log(`   Step 1: Waiting for first agent message...`);
  try {
    await page.waitForSelector(
      '[data-testid="message"][data-role="assistant"]',
      { timeout: 120000 },
    );
    console.log(`   ✅ Agent message appeared`);
  } catch (e) {
    console.log(`   ❌ No agent message after 120s: ${e}`);
    throw e;
  }

  // Inspect current state
  await inspectStreamingAttributes(
    page,
    `${messageLabel} - after message appears`,
  );
  await checkPendingRequests(page, `${messageLabel} - after message appears`);

  // STEP 2: Wait for streaming to complete
  console.log(`   Step 2: Waiting for streaming to complete...`);

  try {
    // Use waitForFunction instead of waitForSelector for more control
    await page.waitForFunction(
      () => {
        const messages = document.querySelectorAll(
          '[data-testid="message"][data-role="assistant"]',
        );
        const hasNonStreaming = Array.from(messages).some(
          (msg) => msg.getAttribute("data-streaming") !== "true",
        );

        if (hasNonStreaming) {
          console.log("Found non-streaming message!");
        } else {
          console.log(`All ${messages.length} messages still streaming...`);
        }

        return hasNonStreaming;
      },
      { timeout: 120000, polling: 1000 },
    ); // Check every second

    console.log(`   ✅ Streaming completed`);
  } catch (e) {
    console.log(`   ❌ Streaming did not complete after 120s: ${e}`);
    await inspectStreamingAttributes(page, `${messageLabel} - TIMEOUT`);
    throw e;
  }

  // Inspect post-streaming state
  await inspectStreamingAttributes(
    page,
    `${messageLabel} - after streaming completes`,
  );
  await checkPendingRequests(
    page,
    `${messageLabel} - after streaming completes`,
  );

  // STEP 3: Wait for content stability
  console.log(`   Step 3: Waiting 3s for content stability...`);
  await page.waitForTimeout(3000);

  console.log(`   ✅ Agent response complete for ${messageLabel}\n`);
}

/**
 * Open tool dropdowns with detailed logging
 */
async function openToolDropdowns(page: Page, messageLabel: string) {
  console.log(`\n🔧 [${messageLabel}] Opening tool dropdowns...`);

  // Wait for tool interactions to exist
  try {
    await page.waitForSelector(".tool-interaction__details summary", {
      timeout: 5000,
    });
    console.log("   ✅ Tool interaction summaries found");
  } catch (e) {
    console.log(
      "   ⚠️  No tool interactions found - skipping dropdown opening",
    );
    return;
  }

  await page.waitForTimeout(1000);

  const summaries = page.locator(".tool-interaction__details summary");
  const count = await summaries.count();

  console.log(`   Found ${count} tool dropdowns to open`);

  for (let i = 0; i < count; i++) {
    try {
      const summary = summaries.nth(i);
      const text = await summary.innerText();
      const isVisible = await summary.isVisible();

      console.log(`   Dropdown ${i}: "${text}" (visible: ${isVisible})`);

      if (isVisible) {
        await summary.click();
        await page.waitForTimeout(300);
        console.log(`     ✅ Clicked`);
      }
    } catch (e) {
      console.log(`     ⚠️  Could not open dropdown ${i}: ${e}`);
    }
  }

  if (count > 0) {
    console.log("   ⏳ Showing expanded tool details for 5 seconds...");
    await page.waitForTimeout(5000);
  }

  console.log(`   ✅ Tool dropdowns handled\n`);
}

test.describe("Daniel Demo: Memory Capabilities (DEBUG)", () => {
  let messageCount = 0;

  test.beforeEach(async ({ page }) => {
    // Enable console log capture
    page.on("console", (msg) => {
      const text = msg.text();
      if (
        text.includes("[Agent]") ||
        text.includes("[Streaming]") ||
        text.includes("[Tool]")
      ) {
        console.log(`🌐 Frontend: ${text}`);
      }
    });

    // Monitor network responses
    page.on("response", (response) => {
      const url = response.url();
      if (url.includes("/chat/") || url.includes("/api/")) {
        console.log(`📡 Network: ${response.status()} ${url.split("/").pop()}`);
      }
    });

    await page.goto("/", { waitUntil: "networkidle" });

    await page.getByRole("textbox", { name: "Email" }).fill(DEMO_EMAIL);
    await page.getByRole("textbox", { name: "Password" }).fill(DEMO_PASSWORD);
    await page.getByRole("button", { name: /sign in/i }).click();

    await expect(
      page.getByRole("heading", {
        name: new RegExp(`Welcome back, Daniel`, "i"),
      }),
    ).toBeVisible({ timeout: 10000 });

    await logMemoryUsage(page, "after login");
    await page.waitForTimeout(2000);
  });

  test("Complete Demo: Both Memory Scenarios (DEBUG)", async ({ page }) => {
    console.log("\n🎬 ============================================");
    console.log("🎬 Starting DEBUG Complete Memory Demo");
    console.log("🎬 ============================================\n");

    try {
      // ===== SCENARIO 1: Golf Course Visitor Recall =====
      console.log("\n📍 ===== SCENARIO 1: Golf Course Visitor Recall =====\n");

      console.log("📋 Creating new conversation...");
      await page.locator(".new-chat-button").click();
      await page.waitForTimeout(1000);
      await logMemoryUsage(page, "after new chat");

      // Message 1
      messageCount++;
      console.log(
        `\n📝 === MESSAGE ${messageCount}: Phoenix golf analysis ===`,
      );
      await typeSlowly(
        page,
        "I'm planning the Dallas launch strategy for our new golf line. Can you remind me what we learned about golfer behavior in Phoenix? Specifically the before and after visit patterns to convenience stores and gas stations?",
      );

      await page.waitForTimeout(1000);
      const sendButton = page
        .locator('button[type="submit"]')
        .or(page.getByRole("button", { name: /send/i }));
      await sendButton.click();
      console.log("✅ Send button clicked");

      await page.waitForTimeout(PAUSE_AFTER_MESSAGE);
      await logMemoryUsage(page, `after message ${messageCount} sent`);

      await waitForAgentResponse(page, `Message ${messageCount}`);
      await logMemoryUsage(page, `after message ${messageCount} response`);

      await expect(
        page.locator("text=search_past_conversations"),
      ).toBeVisible();
      console.log("✅ search_past_conversations tool visible");

      await openToolDropdowns(page, `Message ${messageCount}`);
      await page.waitForTimeout(2000);

      // Message 2
      messageCount++;
      console.log(
        `\n📝 === MESSAGE ${messageCount}: Follow-up about volumes ===`,
      );
      await typeSlowly(
        page,
        "Thanks. What were the exact monthly visit numbers for those top Phoenix golf courses we identified - TPC Scottsdale and the others?",
      );

      await page.waitForTimeout(1000);
      const sendButton2 = page
        .locator('button[type="submit"]')
        .or(page.getByRole("button", { name: /send/i }));
      await sendButton2.click();
      console.log("✅ Send button clicked");

      await page.waitForTimeout(PAUSE_AFTER_MESSAGE);
      await logMemoryUsage(page, `after message ${messageCount} sent`);

      await waitForAgentResponse(page, `Message ${messageCount}`);
      await logMemoryUsage(page, `after message ${messageCount} response`);

      await openToolDropdowns(page, `Message ${messageCount}`);
      await page.waitForTimeout(2000);

      console.log("\n✅ ===== SCENARIO 1 COMPLETED =====\n");

      // Wait before scenario 2
      console.log("⏸️  Pausing 5 seconds before next scenario...\n");
      await page.waitForTimeout(5000);

      // ===== SCENARIO 2: Outlet Ranking with POI Memory =====
      console.log(
        "\n📍 ===== SCENARIO 2: Outlet Ranking with POI Memory =====\n",
      );

      console.log("📋 Continuing in same conversation...");
      await page.waitForTimeout(1000);

      // Message 3
      messageCount++;
      console.log(`\n📝 === MESSAGE ${messageCount}: Tracked locations ===`);
      await typeSlowly(
        page,
        "What golf locations am I currently tracking? Show me my saved places.",
      );

      await page.waitForTimeout(1000);
      const sendButton3 = page
        .locator('button[type="submit"]')
        .or(page.getByRole("button", { name: /send/i }));
      await sendButton3.click();
      console.log("✅ Send button clicked");

      await page.waitForTimeout(PAUSE_AFTER_MESSAGE);
      await logMemoryUsage(page, `after message ${messageCount} sent`);

      await waitForAgentResponse(page, `Message ${messageCount}`);
      await logMemoryUsage(page, `after message ${messageCount} response`);

      await expect(
        page
          .locator(".tool-interaction__name", { hasText: "manage_user_memory" })
          .first(),
      ).toBeVisible();
      console.log("✅ manage_user_memory tool visible");

      await openToolDropdowns(page, `Message ${messageCount}`);
      await page.waitForTimeout(2000);

      // Message 4
      messageCount++;
      console.log(
        `\n📝 === MESSAGE ${messageCount}: Topgolf analysis details ===`,
      );
      await typeSlowly(
        page,
        "We analyzed Topgolf Scottsdale a few days ago with nearby convenience stores. What were the overlap percentages for that 7-Eleven and the other top outlets?",
      );

      await page.waitForTimeout(1000);
      const sendButton4 = page
        .locator('button[type="submit"]')
        .or(page.getByRole("button", { name: /send/i }));
      await sendButton4.click();
      console.log("✅ Send button clicked");

      await page.waitForTimeout(PAUSE_AFTER_MESSAGE);
      await logMemoryUsage(page, `after message ${messageCount} sent`);

      await waitForAgentResponse(page, `Message ${messageCount}`);
      await logMemoryUsage(page, `after message ${messageCount} response`);

      await expect(
        page
          .locator(".tool-interaction__name", {
            hasText: "search_past_conversations",
          })
          .first(),
      ).toBeVisible();
      console.log("✅ search_past_conversations tool visible");

      await openToolDropdowns(page, `Message ${messageCount}`);
      await page.waitForTimeout(2000);

      // Message 5
      messageCount++;
      console.log(`\n📝 === MESSAGE ${messageCount}: Add launch fact ===`);
      await typeSlowly(
        page,
        "Good. Add a note that we launched the golf line at that 7-Eleven Scottsdale Rd location last week.",
      );

      await page.waitForTimeout(1000);
      const sendButton5 = page
        .locator('button[type="submit"]')
        .or(page.getByRole("button", { name: /send/i }));
      await sendButton5.click();
      console.log("✅ Send button clicked");

      await page.waitForTimeout(PAUSE_AFTER_MESSAGE);
      await logMemoryUsage(page, `after message ${messageCount} sent`);

      await waitForAgentResponse(page, `Message ${messageCount}`);
      await logMemoryUsage(page, `after message ${messageCount} response`);

      await expect(
        page.locator(".tool-interaction__name").first(),
      ).toBeVisible();
      console.log("✅ Fact storage tool visible");

      await openToolDropdowns(page, `Message ${messageCount}`);
      await page.waitForTimeout(2000);

      // Message 6
      messageCount++;
      console.log(`\n📝 === MESSAGE ${messageCount}: Full memory view ===`);
      await typeSlowly(
        page,
        "Show me all the locations and facts you've stored about the golf launch project.",
      );

      await page.waitForTimeout(1000);
      const sendButton6 = page
        .locator('button[type="submit"]')
        .or(page.getByRole("button", { name: /send/i }));
      await sendButton6.click();
      console.log("✅ Send button clicked");

      await page.waitForTimeout(PAUSE_AFTER_MESSAGE);
      await logMemoryUsage(page, `after message ${messageCount} sent`);

      await waitForAgentResponse(page, `Message ${messageCount}`);
      await logMemoryUsage(page, `after message ${messageCount} response`);

      await page.waitForTimeout(4000);

      console.log("\n✅ ===== SCENARIO 2 COMPLETED =====\n");

      console.log("\n🎉 ============================================");
      console.log("🎉 COMPLETE DEBUG DEMO FINISHED");
      console.log("🎉 ============================================\n");
    } catch (error) {
      console.error("\n❌ ============================================");
      console.error("❌ DEMO FAILED WITH ERROR");
      console.error("❌ ============================================");
      console.error(error);

      // Final state inspection
      await logMemoryUsage(page, "FAILURE STATE");
      await inspectStreamingAttributes(page, "FAILURE STATE");
      await checkPendingRequests(page, "FAILURE STATE");

      throw error;
    }
  });
});
