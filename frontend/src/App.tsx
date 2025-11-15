import "./App.css";
import LoginForm from "./components/LoginForm";

function App() {
  return (
    <div className="app">
      <header className="app__header">
        <h1>memAgent Demo</h1>
        <p className="app__subtitle">
          Sign in to continue to your AI workspace.
        </p>
      </header>
      <main className="app__main">
        <LoginForm />
      </main>
    </div>
  );
}

export default App;
