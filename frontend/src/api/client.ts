type ApiAwareGlobal = typeof globalThis & {
  __API_BASE_URL__?: string;
};

function getApiBaseUrl(): string {
  const envValue =
    (typeof process !== "undefined"
      ? process.env.VITE_API_BASE_URL
      : undefined) ?? import.meta.env.VITE_API_BASE_URL;
  const runtimeValue = (globalThis as ApiAwareGlobal).__API_BASE_URL__;
  return runtimeValue ?? envValue ?? "http://localhost:8000";
}

export type User = {
  id: string;
  email: string;
  display_name: string;
  role: string | null;
  created_at: string;
  updated_at: string;
};

export type LoginResponse = {
  access_token: string;
  token_type: string;
  user: User;
};

export type ChatResponse = {
  reply: string;
};

export type Message = {
  id: string;
  conversation_id: string;
  role: string;
  content: string;
  created_at: string;
};

export type Conversation = {
  id: string;
  user_id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
};

export type CreateConversationResponse = {
  id: string;
  created_at: string;
};

export type ConversationListResponse = {
  conversations: Conversation[];
};

export type MessageListResponse = {
  messages: Message[];
};

export type SendMessageResponse = {
  user_message: Message;
  assistant_message: Message;
};

type StreamedChunkEvent = {
  type: "chunk";
  content: string;
};

type StreamedUserMessageEvent = {
  type: "user_message";
  message: Message;
};

type StreamedAssistantMessageEvent = {
  type: "assistant_message";
  message: Message;
};

export type StreamedChatEvent =
  | StreamedChunkEvent
  | StreamedUserMessageEvent
  | StreamedAssistantMessageEvent;

export async function login(
  email: string,
  password: string,
): Promise<LoginResponse> {
  const response = await fetch(`${getApiBaseUrl()}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Unable to sign in");
  }

  return response.json() as Promise<LoginResponse>;
}

export async function fetchCurrentUser(token: string): Promise<User> {
  const response = await fetch(`${getApiBaseUrl()}/auth/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error("Failed to fetch user");
  }

  return response.json() as Promise<User>;
}

export async function sendChatMessage(
  token: string,
  message: string,
): Promise<ChatResponse> {
  const response = await fetch(`${getApiBaseUrl()}/chat/messages`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message }),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "Chat failed");
  }

  return response.json() as Promise<ChatResponse>;
}

export async function createConversation(
  token: string,
): Promise<CreateConversationResponse> {
  const response = await fetch(`${getApiBaseUrl()}/chat/conversations`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error("Failed to create conversation");
  }

  return response.json() as Promise<CreateConversationResponse>;
}

export async function getConversations(
  token: string,
): Promise<ConversationListResponse> {
  const response = await fetch(`${getApiBaseUrl()}/chat/conversations`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error("Failed to fetch conversations");
  }

  return response.json() as Promise<ConversationListResponse>;
}

export async function getConversationMessages(
  token: string,
  conversationId: string,
): Promise<MessageListResponse> {
  const response = await fetch(
    `${getApiBaseUrl()}/chat/conversations/${conversationId}/messages`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
  );

  if (!response.ok) {
    throw new Error("Failed to fetch messages");
  }

  return response.json() as Promise<MessageListResponse>;
}

export async function sendMessageToConversation(
  token: string,
  conversationId: string,
  content: string,
): Promise<SendMessageResponse> {
  const response = await fetch(
    `${getApiBaseUrl()}/chat/conversations/${conversationId}/messages`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ content }),
    },
  );

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "Failed to send message");
  }

  return response.json() as Promise<SendMessageResponse>;
}

export async function streamMessageToConversation(
  token: string,
  conversationId: string,
  content: string,
  onEvent: (event: StreamedChatEvent) => void,
): Promise<void> {
  const response = await fetch(
    `${getApiBaseUrl()}/chat/conversations/${conversationId}/messages/stream`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
        Accept: "text/event-stream",
      },
      body: JSON.stringify({ content }),
    },
  );

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "Failed to send message");
  }

  if (!response.body) {
    throw new Error("No response body for stream");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      const remaining = buffer.trim();
      if (remaining.startsWith("data:")) {
        const data = remaining.slice(5).trim();
        if (data !== "[DONE]") {
          onEvent(JSON.parse(data) as StreamedChatEvent);
        }
      }
      break;
    }

    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() ?? "";

    for (const event of events) {
      const line = event.trim();
      if (!line.startsWith("data:")) continue;
      const data = line.slice(5).trim();
      if (data === "[DONE]") {
        return;
      }
      onEvent(JSON.parse(data) as StreamedChatEvent);
    }
  }
}
