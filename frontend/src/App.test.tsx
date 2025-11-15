import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import App from "./App";

describe("App", () => {
  it("allows a user to sign in and receive a chat response", async () => {
    const user = userEvent.setup();
    render(<App />);

    const emailInput = await screen.findByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole("button", { name: /sign in/i });

    await user.type(emailInput, "daniel.insights@goldtobacco.com");
    await user.type(passwordInput, "test-password");
    await user.click(submitButton);

    const welcomeHeading = await screen.findByRole("heading", {
      name: /welcome back/i,
    });
    expect(welcomeHeading).toBeInTheDocument();

    const chatInput = screen.getByLabelText(/ask a question/i);
    await user.type(chatInput, "Hello there");
    const sendButton = screen.getByRole("button", { name: /send/i });
    await user.click(sendButton);

    const reply = await screen.findByText(/hi daniel/i, undefined, {
      timeout: 5000,
    });
    expect(reply).toBeInTheDocument();
  });
});
