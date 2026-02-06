import { useState } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function App() {
  const [input, setInput] = useState('')
  const [response, setResponse] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim()) return
    setLoading(true)
    setError(null)
    setResponse(null)
    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input.trim() }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || res.statusText)
      }
      const data = await res.json()
      setResponse(data.response)
      setInput('')
    } catch (err) {
      setError(err.message || 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        background: '#ebe6f2',
        fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        padding: '2rem 1rem',
      }}
    >
      <div style={{ width: '100%', maxWidth: 480 }}>
        <h1
          style={{
            margin: '0 0 0.25rem 0',
            fontSize: '1.5rem',
            fontWeight: 600,
            color: '#2c2c2c',
          }}
        >
          Bloom Supplements Customer Support
        </h1>
        <p
          style={{
            margin: '0 0 1.5rem 0',
            fontSize: '0.9375rem',
            color: '#5a5a5a',
          }}
        >
          Chat to BloomBot: ask questions about refunds, returns or what to do if you didn't like your order.
        </p>
        <form
          onSubmit={handleSubmit}
          style={{
            display: 'flex',
            gap: '0.5rem',
            marginBottom: '1rem',
          }}
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="How can we help you?"
            disabled={loading}
            style={{
              flex: 1,
              padding: '0.75rem 1rem',
              fontSize: '1rem',
              border: '1px solid #c9c6c2',
              borderRadius: 10,
              background: '#fff',
              color: '#2c2c2c',
            }}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            style={{
              padding: '0.75rem 1.25rem',
              fontSize: '1rem',
              fontWeight: 500,
              background: loading ? '#9a9896' : '#4a4a4a',
              color: '#fff',
              border: 'none',
              borderRadius: 10,
              cursor: loading ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? 'Sending…' : 'Send'}
          </button>
        </form>
        {error && (
          <p
            style={{
              color: '#b91c1c',
              marginBottom: '1rem',
              fontSize: '0.9375rem',
            }}
          >
            {error}
          </p>
        )}
        {response !== null && (
          <div
            style={{
              padding: '1.25rem 1rem',
              background: '#fff',
              borderRadius: 12,
              border: '1px solid #d4d1cc',
              boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
            }}
          >
            <strong style={{ color: '#2c2c2c' }}>BloomBot:</strong>{' '}
            <span style={{ whiteSpace: 'pre-wrap', color: '#3d3d3d' }}>
              {response}
            </span>
          </div>
        )}
      </div>
      <div
        style={{
          width: '100%',
          maxWidth: 480,
          marginTop: '2rem',
          paddingTop: '1rem',
          borderTop: '1px solid #d4d1cc',
          fontSize: '0.875rem',
          color: '#5a5a5a',
        }}
      >
<<<<<<< HEAD
        Built by Shalaka Bapat. Test out BloomBot by asking a question about your order. Note this is a single-turn demo.{' '}
        <a
          href="https://github.com/sbapat19/cx_agent"
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: '#4a4a4a', textDecoration: 'underline' }}
        >
          View source code on GitHub
        </a>
=======
        <p style={{ margin: '0 0 0.75rem 0' }}>
          Built by Shalaka Bapat.{' '}
          <a
            href="https://github.com/sbapat19/cx_agent"
            target="_blank"
            rel="noopener noreferrer"
            style={{ color: '#4a4a4a', textDecoration: 'underline' }}
          >
            View source code on GitHub
          </a>
          .
        </p>
        <p style={{ margin: '0 0 0.75rem 0' }}>
          BloomBot is an AI-agent powered chatbot for a hypothetical supplements brand, powered by two agents. The first interprets the customer's intent, then branches to a specialist agent for the response.
        </p>
        <p style={{ margin: 0 }}>
          The system was built with React on the frontend and Python (FastAPI + LangGraph) on the backend. I improved it iteratively by using an eval set to identify and fix common routing errors, especially on ambiguous refund requests. Enjoy!
        </p>
>>>>>>> 3e2b194 (Improve homepage description.)
      </div>
    </div>
  )
}

export default App
