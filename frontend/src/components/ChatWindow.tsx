import React, { type FormEvent, useEffect, useState } from "react";
import Markdown from "react-markdown";

import {
  getConversationMessages,
  streamMessageToConversation,
  type Message,
  type StreamedChatEvent,
  type User,
} from "../api/client";
import { ToolInteraction } from "./ToolInteraction";

type ChatMessage = {
  id: string;
  sender: "user" | "assistant";
  text: string;
  streaming?: boolean;
  tool_metadata?: Message["tool_metadata"];
  pending_tools?: Array<{
    tool_id: string;
    tool_name: string;
    input: Record<string, unknown>;
    result?: unknown;
    is_error?: boolean;
    is_complete?: boolean;
  }>;
};

type ChatWindowProps = {
  user: User;
  token: string;
  conversationId: string | null;
  onLogout: () => void;
  onConversationUpdated?: () => void;
};

export default function ChatWindow({
  user,
  token,
  conversationId,
  onLogout,
  onConversationUpdated,
}: ChatWindowProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!conversationId) {
      setMessages([]);
      setInput("");
      return;
    }

    setInput("");
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
            tool_metadata: msg.tool_metadata,
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
      tool_metadata: null,
    };

    const assistantPlaceholder: ChatMessage = {
      id: assistantTempId,
      sender: "assistant",
      text: "",
      streaming: true,
      tool_metadata: null,
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
                  ? {
                      ...msg,
                      id: event.message.id,
                      text: event.message.content,
                      streaming: false,
                      tool_metadata: event.message.tool_metadata,
                    }
                  : msg,
              ),
            );
            return;
          }

          if (event.type === "tool_use_start") {
            setMessages((current) =>
              current.map((msg) =>
                msg.id === assistantTempId
                  ? {
                      ...msg,
                      pending_tools: [
                        ...(msg.pending_tools || []),
                        {
                          tool_id: event.tool_id,
                          tool_name: event.tool_name,
                          input: event.input,
                          is_complete: false,
                        },
                      ],
                    }
                  : msg,
              ),
            );
            return;
          }

          if (event.type === "tool_result") {
            setMessages((current) =>
              current.map((msg) =>
                msg.id === assistantTempId
                  ? {
                      ...msg,
                      pending_tools: (msg.pending_tools || []).map((tool) =>
                        tool.tool_id === event.tool_id
                          ? {
                              ...tool,
                              result: event.result,
                              is_error: event.is_error,
                              is_complete: true,
                            }
                          : tool,
                      ),
                    }
                  : msg,
              ),
            );
            return;
          }

          if (event.type === "chunk") {
            setMessages((current) =>
              current.map((msg) =>
                msg.id === assistantTempId
                  ? {
                      ...msg,
                      text: `${msg.text}${event.content}`,
                      streaming: true,
                    }
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
                      tool_metadata: event.message.tool_metadata,
                      pending_tools: undefined,
                    }
                  : msg,
              ),
            );
            onConversationUpdated?.();
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
          messages.map((message, index) => (
            <React.Fragment key={message.id}>
              <div
                className={`chat__message chat__message--${message.sender}`}
                data-streaming={message.streaming ? "true" : "false"}
                data-testid="message"
                data-role={message.sender}
              >
                <span className="chat__message-label">
                  {message.sender === "user" ? user.display_name : "Assistant"}
                </span>
                <div className="chat__message-text">
                  <Markdown>{message.text}</Markdown>
                </div>
              </div>

              {/* Render pending tools (during streaming) */}
              {message.sender === "assistant" &&
                message.pending_tools &&
                message.pending_tools.length > 0 && (
                  <div
                    className="tool-interactions"
                    key={`pending-${message.id}`}
                  >
                    {message.pending_tools.map((tool) => {
                      return (
                        <React.Fragment key={tool.tool_id}>
                          <ToolInteraction
                            interaction={{
                              type: "tool_use",
                              id: tool.tool_id,
                              name: tool.tool_name,
                              input: tool.input,
                            }}
                          />
                          {tool.is_complete && (
                            <ToolInteraction
                              interaction={{
                                type: "tool_result",
                                tool_use_id: tool.tool_id,
                                name: tool.tool_name,
                                content: tool.result,
                                is_error: tool.is_error,
                              }}
                            />
                          )}
                        </React.Fragment>
                      );
                    })}
                  </div>
                )}

              {/* Render tool interactions after the user message that triggered them */}
              {message.sender === "user" &&
                index + 1 < messages.length &&
                messages[index + 1].tool_metadata?.tool_interactions &&
                (messages[index + 1].tool_metadata?.tool_interactions?.length ??
                  0) > 0 && (
                  <div
                    className="tool-interactions"
                    key={`tools-${message.id}`}
                  >
                    {messages[index + 1].tool_metadata?.tool_interactions?.map(
                      (interaction, idx) => {
                        return (
                          <ToolInteraction
                            key={idx}
                            interaction={interaction}
                          />
                        );
                      },
                    )}
                  </div>
                )}
            </React.Fragment>
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
          data-testid="message-input"
        />
        <div className="chat__actions">
          <button
            className="chat__send"
            type="submit"
            disabled={isSending}
            data-testid="send-button"
          >
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
