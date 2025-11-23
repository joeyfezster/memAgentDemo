import { test, expect } from "@playwright/test";

const TEST_USER_EMAIL = "sarah@chickfilb.com";
const TEST_USER_PASSWORD = "changeme123";
const TEST_USER_NAME = "Sarah";

test.describe("Conversation History", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/", { waitUntil: "networkidle" });
    await page.getByRole("textbox", { name: "Email" }).fill(TEST_USER_EMAIL);
    await page
      .getByRole("textbox", { name: "Password" })
      .fill(TEST_USER_PASSWORD);
    await page.getByRole("button", { name: /sign in/i }).click();
    await expect(
      page.getByRole("heading", {
        name: new RegExp(`Welcome back, ${TEST_USER_NAME}`, "i"),
      }),
    ).toBeVisible({
      timeout: 10000,
    });
  });

  test("should display seeded conversations in sidebar", async ({ page }) => {
    await test.step("Wait for conversations to load", async () => {
      await page.waitForSelector("[data-testid='conversation-list']", {
        timeout: 5000,
      });
    });

    await test.step("Verify seeded conversations appear", async () => {
      const conversationItems = page.locator(
        "[data-testid='conversation-item']",
      );
      await expect(conversationItems).toHaveCount(3, { timeout: 5000 });

      await expect(page.getByText(/Python async patterns/i)).toBeVisible();
      await expect(
        page.getByText(/Project planning discussion/i),
      ).toBeVisible();
      await expect(
        page.getByText(/Debugging database connection/i),
      ).toBeVisible();
    });
  });

  test("should load messages when clicking a conversation", async ({
    page,
  }) => {
    await test.step("Click on first conversation", async () => {
      await page.waitForSelector("[data-testid='conversation-list']", {
        timeout: 5000,
      });
      const firstConversation = page
        .locator("[data-testid='conversation-item']")
        .first();
      await firstConversation.click();
    });

    await test.step("Verify messages load in correct order", async () => {
      await page.waitForSelector("[data-testid='message']", {
        timeout: 5000,
      });
      const messages = page.locator("[data-testid='message']");
      await expect(messages).toHaveCount(4, { timeout: 5000 });

      await expect(
        page.getByText(/Can you explain how asyncio works in Python/i),
      ).toBeVisible();
      await expect(
        page.getByText(/Asyncio is Python's built-in library/i),
      ).toBeVisible();
    });
  });

  test("should maintain conversation continuity with agent memory", async ({
    page,
  }) => {
    await test.step("Create new conversation", async () => {
      await page.locator(".new-chat-button").click();
      await page.waitForSelector("[data-testid='message-input']", {
        timeout: 5000,
      });
    });

    await test.step("Introduce user name", async () => {
      const messageInput = page.locator("[data-testid='message-input']");
      await messageInput.fill("Hi, my name is Joe");
      await page.locator("[data-testid='send-button']").click();

      await expect(page.getByText("Hi, my name is Joe")).toBeVisible({
        timeout: 5000,
      });

      // Wait for agent response
      await page.waitForTimeout(2000);
    });

    await test.step("Ask agent to recall user name", async () => {
      const messageInput = page.locator("[data-testid='message-input']");
      await messageInput.fill("What's my name?");
      await page.locator("[data-testid='send-button']").click();

      await expect(page.getByText("What's my name?")).toBeVisible({
        timeout: 5000,
      });
    });

    await test.step("Verify agent remembers the name", async () => {
      // Wait for agent response to the "What's my name?" question
      await page.waitForTimeout(3000);

      // Get all agent messages (not user messages)
      const agentMessages = page.locator(
        "[data-testid='message'][data-role='agent']",
      );

      // Get the last agent message (response to "What's my name?")
      const lastAgentMessage = agentMessages.last();

      // Verify the last agent message contains "Joe"
      await expect(lastAgentMessage).toContainText(/joe/i, {
        timeout: 10000,
      });
    });
  });

  test("should append new message to conversation", async ({ page }) => {
    // Tests appending messages to an existing conversation loaded from history
    await test.step("Select a conversation", async () => {
      await page.waitForSelector("[data-testid='conversation-list']", {
        timeout: 5000,
      });
      const conversation = page
        .locator("[data-testid='conversation-item']")
        .first();
      await conversation.click();
      await page.waitForSelector("[data-testid='message']", {
        timeout: 5000,
      });
    });

    await test.step("Send a new message", async () => {
      const messageInput = page.locator("[data-testid='message-input']");
      await messageInput.fill("This is a test message");
      await page.locator("[data-testid='send-button']").click();
    });

    await test.step("Verify new message appears", async () => {
      await expect(page.getByText("This is a test message")).toBeVisible({
        timeout: 5000,
      });
    });

    await test.step("Verify assistant response appears", async () => {
      await expect(page.getByText(/hi Sarah/i)).toBeVisible({
        timeout: 5000,
      });
    });
  });

  test("should update conversation list after new message", async ({
    page,
  }) => {
    await test.step("Create new conversation", async () => {
      await page.locator(".new-chat-button").click();
      await page.waitForSelector("[data-testid='message-input']", {
        timeout: 5000,
      });
    });

    await test.step("Send first message", async () => {
      const messageInput = page.locator("[data-testid='message-input']");
      await messageInput.fill("Hello, this is a new conversation");
      await page.locator("[data-testid='send-button']").click();

      await expect(
        page.getByText("Hello, this is a new conversation"),
      ).toBeVisible({
        timeout: 5000,
      });
    });

    await test.step("Verify conversation appears in sidebar", async () => {
      await expect(
        page.locator("[data-testid='conversation-item']"),
      ).toHaveCount(4, { timeout: 5000 });
    });

    await test.step("Send second message to trigger title generation", async () => {
      const messageInput = page.locator("[data-testid='message-input']");
      await messageInput.fill("Follow-up message");
      await page.locator("[data-testid='send-button']").click();

      await expect(page.getByText("Follow-up message")).toBeVisible({
        timeout: 5000,
      });
    });

    await test.step("Verify conversation has generated title", async () => {
      await expect(page.getByText(/Hello, this is a/i)).toBeVisible({
        timeout: 5000,
      });
    });
  });

  test("should maintain message state when switching conversations", async ({
    page,
  }) => {
    let firstConvMessageCount: number;
    let secondConvMessageCount: number;

    await test.step("Select first conversation", async () => {
      await page.waitForSelector("[data-testid='conversation-list']", {
        timeout: 5000,
      });
      const firstConv = page
        .locator("[data-testid='conversation-item']")
        .nth(0);
      await firstConv.click();
      await page.waitForSelector("[data-testid='message']", {
        timeout: 5000,
      });
    });

    await test.step("Record first conversation message count", async () => {
      firstConvMessageCount = await page
        .locator("[data-testid='message']")
        .count();
    });

    await test.step("Switch to second conversation", async () => {
      const secondConv = page
        .locator("[data-testid='conversation-item']")
        .nth(1);
      await secondConv.click();
      await page.waitForTimeout(1000);
    });

    await test.step("Record second conversation initial message count", async () => {
      secondConvMessageCount = await page
        .locator("[data-testid='message']")
        .count();
    });

    await test.step("Send new message in second conversation", async () => {
      const messageInput = page.locator("[data-testid='message-input']");
      await messageInput.fill("Test message in second conversation");
      await page.locator("[data-testid='send-button']").click();

      await expect(
        page.getByText("Test message in second conversation"),
      ).toBeVisible({
        timeout: 5000,
      });

      // Wait for agent response
      await page.waitForTimeout(2000);
    });

    await test.step("Verify second conversation message count increased", async () => {
      const currentSecondConvCount = await page
        .locator("[data-testid='message']")
        .count();
      // Should have 2 more messages (user + agent response)
      expect(currentSecondConvCount).toBe(secondConvMessageCount + 2);
    });

    await test.step("Switch back to first conversation", async () => {
      const firstConv = page
        .locator("[data-testid='conversation-item']")
        .nth(0);
      await firstConv.click();
      await page.waitForTimeout(1000);
    });

    await test.step("Verify first conversation message count unchanged", async () => {
      const currentMessageCount = await page
        .locator("[data-testid='message']")
        .count();
      expect(currentMessageCount).toBe(firstConvMessageCount);
    });
  });

  test("should show empty state for new conversation", async ({ page }) => {
    await test.step("Create new conversation", async () => {
      await page.locator(".new-chat-button").click();
    });

    await test.step("Verify empty state is shown", async () => {
      await expect(page.getByText(/Start the conversation/i)).toBeVisible();
    });
  });
});
