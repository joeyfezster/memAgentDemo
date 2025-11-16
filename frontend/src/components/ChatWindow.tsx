import { type FormEvent, useState } from "react";

import { sendChatMessage, type User } from "../api/client";

type ChatMessage = {
  id: number;
  sender: "user" | "assistant";
  text: string;
};

type ChatWindowProps = {
  user: User;
  token: string;
  onLogout: () => void;
};

export default function ChatWindow({ user, token, onLogout }: ChatWindowProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!input.trim()) {
      return;
    }

    const userMessage: ChatMessage = {
      id: Date.now(),
      sender: "user",
      text: input,
    };

    setMessages((current) => [...current, userMessage]);
    setInput("");
    setError(null);
    setIsSending(true);

    try {
      const response = await sendChatMessage(token, userMessage.text);
      const assistantMessage: ChatMessage = {
        id: Date.now() + 1,
        sender: "assistant",
        text: response.reply,
      };
      setMessages((current) => [...current, assistantMessage]);
    } catch (chatError) {
      const message =
        chatError instanceof Error ? chatError.message : "Something went wrong";
      setError(message);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <section className="chat">
      <header className="chat__header">
        <div>
          <h2 className="chat__title">Welcome back, {user.display_name}</h2>
          <p className="chat__subtitle">
            Persona handle: {user.persona_handle}
          </p>
        </div>
        <button className="chat__logout" type="button" onClick={onLogout}>
          Log out
        </button>
      </header>

      <div className="chat__messages" aria-live="polite">
        {messages.length === 0 && (
          <p className="chat__empty">
            Start the conversation with your AI assistant.
          </p>
        )}
        {messages.map((message) => (
          <div
            key={message.id}
            className={`chat__message chat__message--${message.sender}`}
          >
            <span className="chat__message-label">
              {message.sender === "user" ? user.display_name : "Assistant"}
            </span>
            <p>{message.text}</p>
          </div>
        ))}
      </div>

      <form className="chat__composer" onSubmit={handleSubmit}>
        <label className="chat__label" htmlFor="chat-input">
          Ask a question
        </label>
        <textarea
          id="chat-input"
          name="message"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Type your prompt here..."
          rows={3}
          required
        />
        <div className="chat__actions">
          <button className="chat__send" type="submit" disabled={isSending}>
            {isSending ? "Sending..." : "Send"}
          </button>
        </div>
        {error && (
          <p role="alert" className="chat__error">
            {error}
          </p>
        )}
      </form>
    </section>
  );
}
