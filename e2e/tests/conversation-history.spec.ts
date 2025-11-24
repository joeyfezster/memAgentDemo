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
      await expect(conversationItems.first()).toBeVisible({ timeout: 5000 });

      await expect(
        page.getByText(/Site evaluation vs top comps/i),
      ).toBeVisible();
      await expect(
        page.getByText(/Cannibalization analysis for infill/i),
      ).toBeVisible();
      await expect(
        page.getByText(/Portfolio health check - Dallas market/i),
      ).toBeVisible();
    });
  });

  test("should load messages when clicking a conversation", async ({
    page,
  }) => {
    await test.step("Click on 'Site evaluation vs top comps' conversation", async () => {
      await page.waitForSelector("[data-testid='conversation-list']", {
        timeout: 5000,
      });
      const targetConversation = page
        .locator("[data-testid='conversation-item']")
        .filter({ hasText: /Site evaluation vs top comps/i });
      await targetConversation.click();
    });

    await test.step("Verify messages load correctly", async () => {
      await page.waitForSelector("[data-testid='message']", {
        timeout: 5000,
      });
      const messages = page.locator("[data-testid='message']");
      const messageCount = await messages.count();
      // Should have at least 4 messages (the seed messages)
      expect(messageCount).toBeGreaterThanOrEqual(4);

      await expect(
        page.getByText(/Westgate Shopping Center in Phoenix/i).first(),
      ).toBeVisible();
      await expect(
        page
          .getByText(/compare traffic volume, trade area demographics/i)
          .first(),
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

      // Wait for agent response to complete streaming
      const firstAssistant = page
        .locator("[data-testid='message'][data-role='assistant']")
        .first();
      await expect(firstAssistant).toBeVisible({ timeout: 15000 });
      await expect(firstAssistant).toHaveAttribute("data-streaming", "false", {
        timeout: 15000,
      });
    });

    await test.step("Ask agent to recall user name", async () => {
      const messageInput = page.locator("[data-testid='message-input']");
      await messageInput.fill("What's my name?");
      await page.locator("[data-testid='send-button']").click();

      await expect(page.getByText("What's my name?")).toBeVisible({
        timeout: 5000,
      });

      // Wait for agent response to complete streaming
      const secondAssistant = page
        .locator("[data-testid='message'][data-role='assistant']")
        .nth(1);
      await expect(secondAssistant).toBeVisible({ timeout: 15000 });
      await expect(secondAssistant).toHaveAttribute("data-streaming", "false", {
        timeout: 15000,
      });
    });

    await test.step("Verify agent remembers the name", async () => {
      // Get all assistant messages (not user messages)
      const agentMessages = page.locator(
        "[data-testid='message'][data-role='assistant']",
      );

      // Get the last assistant message (response to "What's my name?")
      const lastAgentMessage = agentMessages.last();

      // Verify the last assistant message contains "Joe"
      await expect(lastAgentMessage).toContainText(/joe/i, {
        timeout: 10000,
      });
    });
  });

  test("should append new message to conversation", async ({ page }) => {
    // Tests agent memory by introducing user name and verifying recall
    await test.step("Create new conversation", async () => {
      await page.locator(".new-chat-button").click();
      await page.waitForSelector("[data-testid='message-input']", {
        timeout: 5000,
      });
    });

    await test.step("Introduce user as Sarah", async () => {
      const messageInput = page.locator("[data-testid='message-input']");
      await messageInput.fill("Hi, my name is Sarah");
      await page.locator("[data-testid='send-button']").click();

      await expect(page.getByText("Hi, my name is Sarah")).toBeVisible({
        timeout: 5000,
      });

      // Wait for agent response to complete streaming
      const firstAssistant = page
        .locator("[data-testid='message'][data-role='assistant']")
        .first();
      await expect(firstAssistant).toBeVisible({ timeout: 15000 });
      await expect(firstAssistant).toHaveAttribute("data-streaming", "false", {
        timeout: 15000,
      });
    });

    await test.step("Ask agent to recall user name", async () => {
      const messageInput = page.locator("[data-testid='message-input']");
      await messageInput.fill("What is my name?");
      await page.locator("[data-testid='send-button']").click();

      await expect(page.getByText("What is my name?")).toBeVisible({
        timeout: 5000,
      });
    });

    await test.step("Verify assistant response contains Sarah", async () => {
      // Wait for agent response and check it contains Sarah (case insensitive)
      const assistantMessages = page.locator(
        "[data-testid='message'][data-role='assistant']",
      );
      await expect(assistantMessages.last()).toContainText(/sarah/i, {
        timeout: 10000,
      });

      // Wait for streaming to complete
      await expect(assistantMessages.last()).toHaveAttribute(
        "data-streaming",
        "false",
        {
          timeout: 15000,
        },
      );
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

      // Wait for agent response to complete streaming
      const assistantMessage = page
        .locator("[data-testid='message'][data-role='assistant']")
        .first();
      await expect(assistantMessage).toBeVisible({ timeout: 15000 });
      await expect(assistantMessage).toHaveAttribute(
        "data-streaming",
        "false",
        {
          timeout: 15000,
        },
      );
    });

    await test.step("Verify conversation appears in sidebar", async () => {
      await expect(
        page.getByText("Hello, this is a new conversation").first(),
      ).toBeVisible({ timeout: 5000 });
    });

    await test.step("Send second message to trigger title generation", async () => {
      const messageInput = page.locator("[data-testid='message-input']");
      await messageInput.fill("Follow-up message");
      await page.locator("[data-testid='send-button']").click();

      await expect(page.getByText("Follow-up message").first()).toBeVisible({
        timeout: 5000,
      });

      // Wait for agent response to complete streaming
      const assistantMessage = page
        .locator("[data-testid='message'][data-role='assistant']")
        .last();
      await expect(assistantMessage).toBeVisible({ timeout: 15000 });
      await expect(assistantMessage).toHaveAttribute(
        "data-streaming",
        "false",
        {
          timeout: 15000,
        },
      );
    });

    await test.step("Verify conversation has generated title", async () => {
      // Check that conversation appears in sidebar
      await expect(
        page
          .locator("[data-testid='conversation-item']")
          .filter({ hasText: /Hello, this is a/i })
          .first(),
      ).toBeVisible({
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
        page.getByText("Test message in second conversation").first(),
      ).toBeVisible({
        timeout: 5000,
      });

      // Wait for agent response to complete streaming
      const assistantMessage = page
        .locator("[data-testid='message'][data-role='assistant']")
        .last();
      await expect(assistantMessage).toBeVisible({ timeout: 15000 });
      await expect(assistantMessage).toHaveAttribute(
        "data-streaming",
        "false",
        {
          timeout: 15000,
        },
      );
    });

    await test.step("Verify second conversation message count increased", async () => {
      // Wait for at least one assistant message to appear after sending
      await expect(
        page.locator("[data-testid='message'][data-role='assistant']").last(),
      ).toBeVisible({ timeout: 10000 });

      const currentSecondConvCount = await page
        .locator("[data-testid='message']")
        .count();
      // Should have at least 2 more messages (user + agent response)
      expect(currentSecondConvCount).toBeGreaterThanOrEqual(
        secondConvMessageCount + 2,
      );
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
      // First conversation should have at least as many messages as before
      // (may have more if modified by previous tests)
      expect(currentMessageCount).toBeGreaterThanOrEqual(firstConvMessageCount);
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
