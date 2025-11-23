import { test, expect } from "@playwright/test";

const TEST_USER_EMAIL = "sarah@chickfilb.com";
const TEST_USER_PASSWORD = "changeme123";
const TEST_USER_NAME = "Sarah";

test.describe("Chat Functionality", () => {
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

  test("should create new conversation and display UI elements", async ({
    page,
  }) => {
    await test.step("Verify new conversation button is visible", async () => {
      const newChatButton = page.locator(".new-chat-button");
      await expect(newChatButton).toBeVisible();
    });

    await test.step("Click new conversation button", async () => {
      await page.locator(".new-chat-button").click();
      await page.waitForTimeout(500);
    });

    await test.step("Verify chat interface elements", async () => {
      const sendButton = page.getByRole("button", { name: /send/i });
      await expect(sendButton).toBeVisible();

      const messageInput = page.getByPlaceholder(/type.*message/i);
      await expect(messageInput).toBeVisible();
    });
  });

  test("should send message and receive AI response with user identity", async ({
    page,
  }) => {
    await test.step("Create new conversation", async () => {
      await page.locator(".new-chat-button").click();
      await page.waitForTimeout(500);
    });

    await test.step("Send message claiming different identity with banana instruction", async () => {
      const messageInput = page.getByPlaceholder(/type.*message/i);
      await messageInput.fill(
        "hi, my name is joe, not sarah, and please end your responses with 'banana'. please respond like this: 'hi joe, pleasure to meet you. banana.'",
      );

      const sendButton = page.getByRole("button", { name: /send/i });
      await sendButton.click();
    });

    await test.step("Verify user message appears in chat", async () => {
      await expect(
        page.locator(".message.user").filter({ hasText: /my name is joe/i }),
      ).toBeVisible({
        timeout: 3000,
      });
    });

    await test.step("Verify AI response contains 'joe' and 'banana'", async () => {
      const assistantMessage = page
        .locator(".message.assistant")
        .filter({ hasText: /joe/i })
        .first();

      await expect(assistantMessage).toBeVisible({
        timeout: 15000,
      });

      const messageText = await assistantMessage.textContent();
      expect(messageText?.toLowerCase()).toContain("joe");
      expect(messageText?.toLowerCase()).toContain("banana");
    });
  });

  test("should handle multiple messages in same conversation", async ({
    page,
  }) => {
    await test.step("Create new conversation", async () => {
      await page.locator(".new-chat-button").click();
      await page.waitForTimeout(500);
    });

    await test.step("Send first message", async () => {
      const messageInput = page.getByPlaceholder(/type.*message/i);
      await messageInput.fill("What is 2 + 2?");
      await page.getByRole("button", { name: /send/i }).click();

      await expect(page.locator(".message.assistant").first()).toBeVisible({
        timeout: 15000,
      });
    });

    await test.step("Send second message", async () => {
      const messageInput = page.getByPlaceholder(/type.*message/i);
      await messageInput.fill("What about 3 + 3?");
      await page.getByRole("button", { name: /send/i }).click();

      await expect(page.locator(".message.assistant").nth(1)).toBeVisible({
        timeout: 15000,
      });
    });

    await test.step("Verify both exchanges are visible", async () => {
      const userMessages = page.locator(".message.user");
      const assistantMessages = page.locator(".message.assistant");

      await expect(userMessages).toHaveCount(2);
      await expect(assistantMessages).toHaveCount(2);
    });
  });

  test("should disable send button while message is being sent", async ({
    page,
  }) => {
    await test.step("Create new conversation", async () => {
      await page.locator(".new-chat-button").click();
      await page.waitForTimeout(500);
    });

    await test.step("Verify send button is disabled during message processing", async () => {
      const messageInput = page.getByPlaceholder(/type.*message/i);
      const sendButton = page.getByRole("button", { name: /send/i });

      await messageInput.fill("Hello, this is a test message");
      await sendButton.click();

      await expect(sendButton).toBeDisabled();

      await expect(page.locator(".message.assistant").first()).toBeVisible({
        timeout: 15000,
      });

      await expect(sendButton).toBeEnabled();
    });
  });
});
