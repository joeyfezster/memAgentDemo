import { test, expect } from "@playwright/test";

const TEST_USER_EMAIL = "sarah@chickfilb.com";
const TEST_USER_PASSWORD = "changeme123";
const TEST_USER_NAME = "Sarah";

test.describe("Login Flow", () => {
  test("should successfully login with valid credentials", async ({ page }) => {
    await test.step("Navigate to application", async () => {
      await page.goto("/", { waitUntil: "networkidle" });
      await expect(
        page.getByRole("heading", { name: "memAgent Demo" }),
      ).toBeVisible();
    });

    await test.step("Login with test user", async () => {
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

    await test.step("Verify chat interface is visible", async () => {
      await expect(page.locator(".new-chat-button")).toBeVisible();
    });
  });

  test("should preserve authentication across page reload", async ({
    page,
  }) => {
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

    await page.reload({ waitUntil: "networkidle" });

    await expect(
      page.getByRole("heading", {
        name: new RegExp(`Welcome back, ${TEST_USER_NAME}`, "i"),
      }),
    ).toBeVisible({
      timeout: 10000,
    });

    await expect(page.locator(".new-chat-button")).toBeVisible();
  });
});
