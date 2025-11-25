import { test, expect, Page } from "@playwright/test";

/**
 * Demo Script Runner for Daniel Persona
 * Showcases memory capabilities with slow, human-paced interactions
 */

const DEMO_EMAIL = "daniel.insights@goldtobacco.com";
const DEMO_PASSWORD = "changeme123";
const TYPING_DELAY_MIN = 25; // ms between characters (60% faster than original)
const TYPING_DELAY_MAX = 74; // ms between characters (60% faster than original)
const PAUSE_AFTER_MESSAGE = 3000; // Wait 3s after sending message before next action

/**
 * Type text slowly like a human
 */
async function typeSlowly(page: Page, text: string) {
  const input = page.getByPlaceholder(/type.*message/i);

  // Ensure input is visible and ready
  await input.waitFor({ state: "visible", timeout: 5000 });
  await input.click();
  await page.waitForTimeout(500); // Wait for focus

  for (const char of text) {
    await page.keyboard.type(char);
    const delay =
      Math.random() * (TYPING_DELAY_MAX - TYPING_DELAY_MIN) + TYPING_DELAY_MIN;
    await page.waitForTimeout(delay);
  }
}

/**
 * Wait for agent response to complete (watch for streaming to finish)
 */
async function waitForAgentResponse(page: Page) {
  // Wait for at least one agent message bubble to appear
  await page.waitForSelector('[data-testid="message"][data-role="assistant"]', {
    timeout: 120000,
  });

  // Wait for streaming to complete - use a more robust check
  // The message might take a moment to update from streaming=true to streaming=false
  try {
    await page.waitForSelector(
      '[data-testid="message"][data-role="assistant"]:not([data-streaming="true"])',
      { timeout: 120000 },
    );
  } catch (e) {
    // Fallback: If streaming attribute doesn't change, wait for content to stabilize
    console.log("⚠️  Streaming attribute did not change, using fallback...");
    await page.waitForTimeout(5000);
  }

  // Wait for streaming animation to stop (checking for stable content)
  await page.waitForTimeout(3000);
}

/**
 * Open all tool interaction dropdowns (details elements) and wait
 */
async function openToolDropdowns(page: Page) {
  // Wait a moment for dropdowns to be fully rendered
  await page.waitForTimeout(1000);

  // Find all summary elements within tool interactions
  const summaries = page.locator(".tool-interaction__details summary");
  const count = await summaries.count();

  console.log(`   Opening ${count} tool dropdowns...`);

  // Click each summary to expand
  for (let i = 0; i < count; i++) {
    try {
      const summary = summaries.nth(i);
      if (await summary.isVisible()) {
        await summary.click();
        await page.waitForTimeout(300);
      }
    } catch (e) {
      console.log(`   ⚠️  Could not open dropdown ${i}: ${e}`);
    }
  }

  // Wait 5 seconds to show the expanded tool details
  if (count > 0) {
    console.log("   ⏳ Showing expanded tool details for 5 seconds...");
    await page.waitForTimeout(5000);
  }
}

test.describe("Daniel Demo: Memory Capabilities", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to login page
    await page.goto("/", { waitUntil: "networkidle" });

    // Fill login form
    await page.getByRole("textbox", { name: "Email" }).fill(DEMO_EMAIL);
    await page.getByRole("textbox", { name: "Password" }).fill(DEMO_PASSWORD);
    await page.getByRole("button", { name: /sign in/i }).click();

    // Wait for chat interface with Daniel's name
    await expect(
      page.getByRole("heading", {
        name: new RegExp(`Welcome back, Daniel`, "i"),
      }),
    ).toBeVisible({ timeout: 10000 });

    // Pause to show successful login
    await page.waitForTimeout(2000);
  });

  test("Complete Demo: Both Memory Scenarios", async ({ page }) => {
    console.log("\n🎬 Starting Complete Memory Demo");

    try {
      // ===== SCENARIO 1: Golf Course Visitor Recall =====
      console.log("\n📍 SCENARIO 1: Golf Course Visitor Recall");
      console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");

      // Create new conversation
      console.log("📋 Creating new conversation...");
      await page.locator(".new-chat-button").click();
      await page.waitForTimeout(1000);

      // Message 1: Ask about Phoenix analysis (should trigger search_past_conversations)
      console.log("📝 User asks about Phoenix golf analysis...");
      await typeSlowly(
        page,
        "I'm planning the Dallas launch strategy for our new golf line. Can you remind me what we learned about golfer behavior in Phoenix? Specifically the before and after visit patterns to convenience stores and gas stations?",
      );

      await page.waitForTimeout(1000);
      // Click send button explicitly instead of pressing Enter
      const sendButton = page
        .locator('button[type="submit"]')
        .or(page.getByRole("button", { name: /send/i }));
      await sendButton.click();
      await page.waitForTimeout(PAUSE_AFTER_MESSAGE);

      // Wait for agent to use search_past_conversations tool
      console.log("🔍 Waiting for agent to search past conversations...");
      await waitForAgentResponse(page);

      // Check for tool interaction visibility
      await expect(
        page
          .locator(".tool-interaction__name", {
            hasText: "search_past_conversations",
          })
          .first(),
      ).toBeVisible();
      console.log("✅ Memory search tool visible in UI");

      // Open tool dropdowns and wait
      await openToolDropdowns(page);

      await page.waitForTimeout(2000); // Additional pause after showing tool details

      // Message 2: Follow-up about specific visit volumes from that analysis
      console.log("📝 User asks follow-up about course volumes...");
      await typeSlowly(
        page,
        "Thanks. What were the exact monthly visit numbers for those top Phoenix golf courses we identified - TPC Scottsdale and the others?",
      );

      await page.waitForTimeout(1000);
      const sendButton2 = page
        .locator('button[type="submit"]')
        .or(page.getByRole("button", { name: /send/i }));
      await sendButton2.click();
      await page.waitForTimeout(PAUSE_AFTER_MESSAGE);

      console.log("⏳ Waiting for agent response from context...");
      await waitForAgentResponse(page);

      // Open any tool dropdowns if present
      await openToolDropdowns(page);

      await page.waitForTimeout(2000);
      console.log("✅ Scenario 1 completed\n");

      // Wait 5 seconds before starting scenario 2
      console.log("⏸️  Pausing 5 seconds before next scenario...\n");
      await page.waitForTimeout(5000);

      // ===== SCENARIO 2: Outlet Ranking with POI Memory =====
      console.log("\n📍 SCENARIO 2: Outlet Ranking with POI Memory");
      console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");

      // Continue in same conversation - no new chat needed
      console.log("📋 Continuing in same conversation...");
      await page.waitForTimeout(1000);

      // Message 3: Ask about tracked POIs (should trigger manage_user_memory get_memory)
      console.log("📝 User asks about tracked locations...");
      await typeSlowly(
        page,
        "What locations have I been tracking for the golf line launch?",
      );

      await page.waitForTimeout(1000);
      const sendButton3 = page
        .locator('button[type="submit"]')
        .or(page.getByRole("button", { name: /send/i }));
      await sendButton3.click();
      await page.waitForTimeout(PAUSE_AFTER_MESSAGE);

      // Wait for manage_user_memory (get_memory) tool
      console.log("🔍 Waiting for agent to retrieve user memory...");
      await waitForAgentResponse(page);

      await expect(
        page
          .locator(".tool-interaction__name", { hasText: "manage_user_memory" })
          .first(),
      ).toBeVisible();
      console.log("✅ User memory tool visible in UI");

      // Open tool dropdowns and wait
      await openToolDropdowns(page);

      await page.waitForTimeout(2000);

      // Message 4: Ask about Topgolf Scottsdale analysis (should trigger search_past_conversations)
      console.log("📝 User asks about Topgolf analysis...");
      await typeSlowly(
        page,
        "We analyzed Topgolf Scottsdale a few days ago with nearby convenience stores. What were the overlap percentages for that 7-Eleven and the other top outlets?",
      );

      await page.waitForTimeout(1000);
      const sendButton4 = page
        .locator('button[type="submit"]')
        .or(page.getByRole("button", { name: /send/i }));
      await sendButton4.click();
      await page.waitForTimeout(PAUSE_AFTER_MESSAGE);

      console.log("🔍 Waiting for agent to search past conversations...");
      await waitForAgentResponse(page);

      await expect(
        page
          .locator(".tool-interaction__name", {
            hasText: "search_past_conversations",
          })
          .first(),
      ).toBeVisible();
      console.log("✅ Memory search combined with POI recall");

      // Open tool dropdowns and wait
      await openToolDropdowns(page);

      await page.waitForTimeout(2000);

      // Message 5: Add launch fact (should trigger manage_user_memory add_poi or add_fact)
      console.log("📝 User adds launch fact...");
      await typeSlowly(
        page,
        "Perfect. I want to add a note that we launched product at that 7-Eleven last week.",
      );

      await page.waitForTimeout(1000);
      const sendButton5 = page
        .locator('button[type="submit"]')
        .or(page.getByRole("button", { name: /send/i }));
      await sendButton5.click();
      await page.waitForTimeout(PAUSE_AFTER_MESSAGE);

      console.log("💾 Waiting for agent to store fact...");
      await waitForAgentResponse(page);

      await expect(
        page.locator(".tool-interaction__name").first(),
      ).toBeVisible();
      console.log("✅ Fact storage tool visible");

      // Open tool dropdowns and wait
      await openToolDropdowns(page);

      await page.waitForTimeout(2000);

      // Message 6: View all stored memory (should trigger manage_user_memory get_memory)
      console.log("📝 User requests full memory view...");
      await typeSlowly(
        page,
        "Show me everything you remember about my golf launch project.",
      );

      await page.waitForTimeout(1000);
      const sendButton6 = page
        .locator('button[type="submit"]')
        .or(page.getByRole("button", { name: /send/i }));
      await sendButton6.click();
      await page.waitForTimeout(PAUSE_AFTER_MESSAGE);

      console.log("📚 Waiting for comprehensive memory retrieval...");
      await waitForAgentResponse(page);

      await page.waitForTimeout(4000);
      console.log("✅ Scenario 2 completed\n");

      console.log("\n🎉 COMPLETE DEMO FINISHED\n");
    } catch (error) {
      console.error("❌ Demo failed with error:", error);
      throw error;
    }
  });
});
