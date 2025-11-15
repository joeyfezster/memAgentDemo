import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import App from "./App";

describe("App", () => {
  it("renders the login form and validates submissions", async () => {
    render(<App />);

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole("button", { name: /sign in/i });

    await userEvent.type(emailInput, "user@example.com");
    await userEvent.type(passwordInput, "password123");
    await userEvent.click(submitButton);

    expect(await screen.findByRole("status")).toHaveTextContent(
      /you are signed in/i,
    );
  });
});
