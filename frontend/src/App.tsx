import { useEffect, useState } from "react";

import "./App.css";
import {
  createConversation,
  fetchCurrentUser,
  getConversations,
  login,
  type Conversation,
  type User,
} from "./api/client";
import ChatWindow from "./components/ChatWindow";
import LoginForm from "./components/LoginForm";
import Sidebar from "./components/Sidebar";
import AgentExplorer from "./components/AgentExplorer/AgentExplorer";

type AuthState = {
  token: string;
  user: User | null;
};

const STORAGE_KEY = "memagent.auth";

function App() {
  const [auth, setAuth] = useState<AuthState | null>(() => {
    if (typeof window === "undefined") {
      return null;
    }
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    try {
      const parsed = JSON.parse(raw) as AuthState;
      return parsed;
    } catch (error) {
      console.warn("Failed to parse stored auth state", error);
      return null;
    }
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [initializing, setInitializing] = useState(true);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<
    string | null
  >(null);
  const [activeView, setActiveView] = useState<"chat" | "agents">("chat");

  useEffect(() => {
    const restoreUser = async () => {
      if (!auth || !auth.token || auth.user || !initializing) {
        setInitializing(false);
        return;
      }
      try {
        const user = await fetchCurrentUser(auth.token);
        const next = { token: auth.token, user };
        setAuth(next);
        if (typeof window !== "undefined") {
          window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
        }
      } catch (restoreError) {
        console.error("Failed to restore session", restoreError);
        setAuth(null);
        if (typeof window !== "undefined") {
          window.localStorage.removeItem(STORAGE_KEY);
        }
      } finally {
        setInitializing(false);
      }
    };

    void restoreUser();
  }, [auth, initializing]);

  useEffect(() => {
    const loadConversations = async () => {
      if (!auth?.token || !auth?.user) {
        setConversations([]);
        setCurrentConversationId(null);
        return;
      }

      try {
        const response = await getConversations(auth.token);
        setConversations(response.conversations);
      } catch (loadError) {
        console.error("Failed to load conversations", loadError);
      }
    };

    void loadConversations();
  }, [auth, currentConversationId]);

  const handleLogin = async (email: string, password: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await login(email, password);
      const next: AuthState = {
        token: response.access_token,
        user: response.user,
      };
      setAuth(next);
      if (typeof window !== "undefined") {
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      }
    } catch (loginError) {
      const message =
        loginError instanceof Error ? loginError.message : "Unable to sign in";
      setError(message);
      throw loginError;
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    setAuth(null);
    setError(null);
    setConversations([]);
    setCurrentConversationId(null);
    setActiveView("chat");
    if (typeof window !== "undefined") {
      window.localStorage.removeItem(STORAGE_KEY);
    }
  };

  const handleNewChat = async () => {
    if (!auth?.token) return;

    try {
      const response = await createConversation(auth.token);
      const newConversation: Conversation = {
        id: response.id,
        user_id: auth.user!.id,
        title: null,
        created_at: response.created_at,
        updated_at: response.created_at,
      };
      setConversations((prev) => [newConversation, ...prev]);
      setCurrentConversationId(response.id);
    } catch (createError) {
      console.error("Failed to create conversation", createError);
    }
  };

  const handleSelectConversation = (id: string) => {
    setCurrentConversationId(id);
  };

  const user = auth?.user ?? null;

  return (
    <div className="app">
      {user ? (
        <>
          <header className="app__nav">
            <div>
              <h1>memAgent Demo</h1>
              <p>Signed in as {user.display_name}</p>
            </div>
            <div className="app__nav-tabs">
              <button
                type="button"
                className={`app__nav-button ${
                  activeView === "chat" ? "is-active" : ""
                }`}
                onClick={() => setActiveView("chat")}
              >
                Chat workspace
              </button>
              <button
                type="button"
                className={`app__nav-button ${
                  activeView === "agents" ? "is-active" : ""
                }`}
                onClick={() => setActiveView("agents")}
              >
                Agents & memories
              </button>
              <button
                type="button"
                className="app__nav-logout"
                onClick={handleLogout}
              >
                Log out
              </button>
            </div>
          </header>
          {activeView === "chat" ? (
            <div className="app-container">
              <Sidebar
                conversations={conversations}
                activeConversationId={currentConversationId}
                onSelectConversation={handleSelectConversation}
                onNewChat={handleNewChat}
              />
              <ChatWindow
                user={user}
                token={auth!.token}
                conversationId={currentConversationId}
              />
            </div>
          ) : (
            <main className="agent-explorer-page">
              <AgentExplorer token={auth!.token} />
            </main>
          )}
        </>
      ) : (
        <>
          <header className="app__header">
            <h1>memAgent Demo</h1>
            <p className="app__subtitle">
              Sign in to continue to your AI workspace.
            </p>
          </header>
          <main className="app__main">
            <LoginForm
              onSubmit={handleLogin}
              loading={loading || initializing}
              error={error}
            />
          </main>
        </>
      )}
    </div>
  );
}

export default App;
