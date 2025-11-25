import { describe, expect, it, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import App from "./App";

describe("App", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });
  it("allows a user to sign in and create a conversation", async () => {
    const user = userEvent.setup();
    render(<App />);

    const emailInput = await screen.findByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole("button", { name: /sign in/i });

    await user.type(emailInput, "daniel.insights@goldtobacco.com");
    await user.type(passwordInput, "test-password");
    await user.click(submitButton);

    const welcomeHeading = await screen.findByRole(
      "heading",
      { name: /welcome back/i },
      { timeout: 10000 },
    );
    expect(welcomeHeading).toBeInTheDocument();

    const newChatButton = await screen.findByRole(
      "button",
      {
        name: /new chat/i,
      },
      { timeout: 5000 },
    );
    expect(newChatButton).toBeInTheDocument();

    await user.click(newChatButton);

    const chatInput = await screen.findByLabelText(
      /ask a question/i,
      {},
      { timeout: 5000 },
    );
    expect(chatInput).toBeInTheDocument();

    await user.type(chatInput, "Hello there");
    const sendButton = screen.getByRole("button", { name: /send/i });
    await user.click(sendButton);

    await waitFor(
      () => {
        const assistantMessages = document.querySelectorAll(
          ".chat__message--assistant p",
        );
        const found = Array.from(assistantMessages).some(
          (el) =>
            /placer/i.test(el.textContent || "") ||
            /daniel/i.test(el.textContent || ""),
        );
        expect(found).toBe(true);
      },
      { timeout: 10000 },
    );

    const conversationInSidebar = await screen.findByText(
      /hello there/i,
      {},
      { timeout: 5000 },
    );
    expect(conversationInSidebar).toBeInTheDocument();
  }, 25000);

  it("allows a user to view previous conversation messages", async () => {
    const user = userEvent.setup();
    render(<App />);

    const emailInput = await screen.findByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole("button", { name: /sign in/i });

    await user.type(emailInput, "daniel.insights@goldtobacco.com");
    await user.type(passwordInput, "test-password");
    await user.click(submitButton);

    const welcomeHeading = await screen.findByRole(
      "heading",
      { name: /welcome back/i },
      { timeout: 10000 },
    );
    expect(welcomeHeading).toBeInTheDocument();

    const newChatButton = await screen.findByRole(
      "button",
      {
        name: /new chat/i,
      },
      { timeout: 5000 },
    );
    await user.click(newChatButton);

    const chatInput = await screen.findByLabelText(
      /ask a question/i,
      {},
      { timeout: 5000 },
    );
    await user.type(chatInput, "First message");
    const sendButton = screen.getByRole("button", { name: /send/i });
    await user.click(sendButton);

    await waitFor(
      () => {
        const assistantMessages = document.querySelectorAll(
          ".chat__message--assistant p",
        );
        const found = Array.from(assistantMessages).some(
          (el) =>
            /placer/i.test(el.textContent || "") ||
            /daniel/i.test(el.textContent || ""),
        );
        expect(found).toBe(true);
      },
      { timeout: 10000 },
    );

    const conversationInSidebar = await screen.findByText(
      /first message/i,
      {},
      { timeout: 5000 },
    );
    expect(conversationInSidebar).toBeInTheDocument();

    await user.click(newChatButton);

    const secondChatInput = await screen.findByLabelText(
      /ask a question/i,
      {},
      { timeout: 5000 },
    );
    await user.type(secondChatInput, "Second conversation");
    const secondSendButton = screen.getByRole("button", { name: /send/i });
    await user.click(secondSendButton);

    await screen.findByText(/second conversation/i, {}, { timeout: 10000 });

    const firstConversationButton = await screen.findByText(
      /first message/i,
      {},
      { timeout: 5000 },
    );
    await user.click(firstConversationButton);

    await waitFor(
      () => {
        const secondMessage = screen.queryByText(/second conversation/i);
        expect(secondMessage).not.toBeInTheDocument();
      },
      { timeout: 5000 },
    );

    await waitFor(
      () => {
        const messages = screen.getAllByText(/first message/i);
        expect(messages.length).toBeGreaterThan(0);
      },
      { timeout: 5000 },
    );

    await waitFor(
      () => {
        const assistantMessages = document.querySelectorAll(
          ".chat__message--assistant p",
        );
        const found = Array.from(assistantMessages).some(
          (el) =>
            /placer/i.test(el.textContent || "") ||
            /daniel/i.test(el.textContent || ""),
        );
        expect(found).toBe(true);
      },
      { timeout: 5000 },
    );
  }, 30000);
});
