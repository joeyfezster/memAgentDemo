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
  persona_handle: string;
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

export type AssignedUser = {
  id: string;
  email: string;
  display_name: string;
};

export type MemoryBlock = {
  id: string;
  label: string | null;
  description: string | null;
  value: string | null;
  limit: number | null;
  read_only: boolean | null;
  block_type: string | null;
  metadata: Record<string, unknown>;
};

export type AgentOverview = {
  id: string;
  name: string | null;
  created_at: string | null;
  updated_at: string | null;
  user: AssignedUser | null;
  memory_blocks: MemoryBlock[];
  metadata: Record<string, unknown>;
};

export type AgentsOverviewResponse = {
  agents: AgentOverview[];
  agent_count: number;
  block_count: number;
  generated_at: string;
};

export type ArchivalEntry = {
  id: string;
  content: string;
  tags: string[];
  created_at: string | null;
  updated_at: string | null;
  metadata: Record<string, unknown>;
};

export type AgentArchivalResponse = {
  agent_id: string;
  entries: ArchivalEntry[];
  requested_limit: number;
  returned_count: number;
};

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

export async function getAgentsOverview(
  token: string,
): Promise<AgentsOverviewResponse> {
  const response = await fetch(`${getApiBaseUrl()}/letta/agents/overview`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "Failed to load agents");
  }

  return response.json() as Promise<AgentsOverviewResponse>;
}

export async function getAgentArchival(
  token: string,
  agentId: string,
  limit = 7,
): Promise<AgentArchivalResponse> {
  const url = new URL(
    `${getApiBaseUrl()}/letta/agents/${agentId}/archival`,
  );
  if (limit) {
    url.searchParams.set("limit", String(limit));
  }

  const response = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "Failed to load archival entries");
  }

  return response.json() as Promise<AgentArchivalResponse>;
}
