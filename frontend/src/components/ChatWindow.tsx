import { type FormEvent, useEffect, useState } from "react";

import {
  getConversationMessages,
  streamMessageToConversation,
  type Message,
  type StreamedChatEvent,
  type User,
} from "../api/client";

type ChatMessage = {
  id: string;
  sender: "user" | "assistant";
  text: string;
  streaming?: boolean;
};

type ChatWindowProps = {
  user: User;
  token: string;
  conversationId: string | null;
  onLogout: () => void;
};

export default function ChatWindow({
  user,
  token,
  conversationId,
  onLogout,
}: ChatWindowProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!conversationId) {
      setMessages([]);
      return;
    }

    let cancelled = false;

    const loadMessages = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await getConversationMessages(token, conversationId);
        if (cancelled) return;

        const chatMessages: ChatMessage[] = response.messages.map(
          (msg: Message) => ({
            id: msg.id,
            sender: msg.role as "user" | "assistant",
            text: msg.content,
            streaming: false,
          }),
        );
        setMessages(chatMessages);
      } catch (loadError) {
        if (cancelled) return;

        const message =
          loadError instanceof Error
            ? loadError.message
            : "Failed to load messages";
        setError(message);
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    loadMessages();

    return () => {
      cancelled = true;
    };
  }, [conversationId, token]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!input.trim() || !conversationId) {
      return;
    }

    const userMessageText = input;
    const tempId = `temp-${Date.now()}`;
    const assistantTempId = `assistant-${Date.now()}`;
    const userMessage: ChatMessage = {
      id: tempId,
      sender: "user",
      text: userMessageText,
      streaming: false,
    };

    const assistantPlaceholder: ChatMessage = {
      id: assistantTempId,
      sender: "assistant",
      text: "",
      streaming: true,
    };

    setMessages((current) => [...current, userMessage, assistantPlaceholder]);
    setInput("");
    setError(null);
    setIsSending(true);

    try {
      await streamMessageToConversation(
        token,
        conversationId,
        userMessageText,
        (event: StreamedChatEvent) => {
          if (event.type === "user_message") {
            setMessages((current) =>
              current.map((msg) =>
                msg.id === tempId
                  ? { ...msg, id: event.message.id, text: event.message.content }
                  : msg,
              ),
            );
            return;
          }

          if (event.type === "chunk") {
            setMessages((current) =>
              current.map((msg) =>
                msg.id === assistantTempId
                  ? { ...msg, text: `${msg.text}${event.content}` }
                  : msg,
              ),
            );
            return;
          }

          if (event.type === "assistant_message") {
            setMessages((current) =>
              current.map((msg) =>
                msg.id === assistantTempId
                  ? {
                      id: event.message.id,
                      sender: "assistant",
                      text: event.message.content,
                      streaming: false,
                    }
                  : msg,
              ),
            );
          }
        },
      );
    } catch (chatError) {
      const message =
        chatError instanceof Error ? chatError.message : "Something went wrong";
      setError(message);
      setMessages((current) =>
        current.filter(
          (msg) => msg.id !== tempId && msg.id !== assistantTempId,
        ),
      );
    } finally {
      setIsSending(false);
    }
  };

  if (!conversationId) {
    return (
      <section className="chat">
        <header className="chat__header">
          <div>
            <h2 className="chat__title">Welcome back, {user.display_name}</h2>
          </div>
          <button className="chat__logout" type="button" onClick={onLogout}>
            Log out
          </button>
        </header>
        <div className="chat__messages">
          <p className="chat__empty">
            Start the conversation with your AI assistant.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="chat">
      <header className="chat__header">
        <div>
          <h2 className="chat__title">Welcome back, {user.display_name}</h2>
        </div>
        <button className="chat__logout" type="button" onClick={onLogout}>
          Log out
        </button>
      </header>

      <div className="chat__messages" aria-live="polite">
        {isLoading && <p className="chat__empty">Loading messages...</p>}
        {!isLoading && messages.length === 0 && (
          <p className="chat__empty">
            Start the conversation with your AI assistant.
          </p>
        )}
        {!isLoading &&
          messages.map((message) => (
            <div
              key={message.id}
              className={`chat__message chat__message--${message.sender}`}
              data-streaming={message.streaming ? "true" : "false"}
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
          placeholder="Type your message here..."
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
