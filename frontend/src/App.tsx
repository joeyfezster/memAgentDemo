import { useEffect, useState } from "react";

import "./App.css";
import { fetchCurrentUser, login, type User } from "./api/client";
import ChatWindow from "./components/ChatWindow";
import LoginForm from "./components/LoginForm";

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

  useEffect(() => {
    const restoreUser = async () => {
      if (!auth || !auth.token || auth.user) {
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
  }, [auth]);

  const handleLogin = async (email: string, password: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await login(email, password);
      const next: AuthState = { token: response.access_token, user: response.user };
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
    if (typeof window !== "undefined") {
      window.localStorage.removeItem(STORAGE_KEY);
    }
  };

  const user = auth?.user ?? null;

  return (
    <div className="app">
      <header className="app__header">
        <h1>memAgent Demo</h1>
        <p className="app__subtitle">
          {user ? "Interact with your AI workspace." : "Sign in to continue to your AI workspace."}
        </p>
      </header>
      <main className="app__main">
        {user ? (
          <ChatWindow user={user} token={auth!.token} onLogout={handleLogout} />
        ) : (
          <LoginForm onSubmit={handleLogin} loading={loading || initializing} error={error} />
        )}
      </main>
    </div>
  );
}

export default App;
