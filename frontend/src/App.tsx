import { useState } from 'react'
import './App.css'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="app">
      <header className="app-header">
        <h1>Memory Agent</h1>
        <p>AI-powered memory management system</p>
      </header>
      <main className="app-main">
        <div className="card">
          <button onClick={() => setCount(count => count + 1)}>
            Count: {count}
          </button>
          <p>
            This is a placeholder for the Memory Agent interface.
          </p>
        </div>
      </main>
    </div>
  )
}

export default App
