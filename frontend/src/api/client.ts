type ApiAwareGlobal = typeof globalThis & {
  __API_BASE_URL__?: string;
};

function getApiBaseUrl(): string {
  const envValue =
    (typeof process !== "undefined" ? process.env.VITE_API_BASE_URL : undefined) ??
    import.meta.env.VITE_API_BASE_URL;
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

export async function login(email: string, password: string): Promise<LoginResponse> {
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
