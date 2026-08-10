import { useState } from 'react'
import { motion } from 'framer-motion'

const API_URL = 'http://localhost:8000'

function App() {
  const [requirement, setRequirement] = useState('')
  const [result, setResult] = useState(null)
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const [loggedIn, setLoggedIn] = useState(false)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loginError, setLoginError] = useState('')

  function handleLogin(event) {
    event.preventDefault()
    setLoginError('')

    if (!username.trim() || !password.trim()) {
      setLoginError('Please enter both username and password.')
      return
    }

    if (username === 'admin' && password === 'password') {
      setLoggedIn(true)
      setUsername('')
      setPassword('')
      setLoginError('')
      return
    }

    setLoginError('Invalid credentials. Use admin / password.')
  }

  if (!loggedIn) {
    return (
      <div className="login-shell">
        <motion.div
          className="login-card"
          initial={{ y: 40, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
        >
          <div className="login-header">
            <span className="badge">AI Software Team</span>
            <h1>Sign in to continue</h1>
            <p>Authenticate before using the AI generation workflow.</p>
          </div>

          <form className="login-form" onSubmit={handleLogin}>
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              placeholder="admin"
            />

            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="password"
            />

            <button type="submit">Login</button>
            {loginError && <div className="error-message">{loginError}</div>}
          </form>
        </motion.div>
      </div>
    )
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')

    if (!requirement.trim()) {
      setError('Please enter a project requirement.')
      return
    }

    setStatus('Generating project...')
    setResult(null)

    try {
      const response = await fetch(`${API_URL}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ requirement }),
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Failed to generate project.')
      }

      const data = await response.json()
      setResult(data)
      setStatus('Project generated successfully!')
    } catch (err) {
      setStatus('')
      setError(err.message)
    }
  }

  return (
    <div className="page-shell">
      <motion.header
        initial={{ y: -80, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.8, ease: 'easeOut' }}
        className="hero"
      >
        <div className="hero-copy">
          <span className="badge">AI Software Team</span>
          <h1>From idea to product with animated AI collaboration.</h1>
          <p>
            Describe your software goal and watch the AI team generate tasks, code,
            review notes, and test plans in a modern frontend with motion.
          </p>
        </div>
        <div className="hero-visual">
          <div className="visual-card">
            <div className="visual-dot top" />
            <div className="visual-line" />
            <div className="visual-dot middle" />
            <div className="visual-line" />
            <div className="visual-dot bottom" />
          </div>
        </div>
      </motion.header>

      <motion.main
        className="content"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6, delay: 0.2 }}
      >
        <section className="form-panel">
          <motion.div
            className="form-card"
            initial={{ scale: 0.98, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.6 }}
          >
            <h2>Start with a requirement</h2>
            <p>Use an open prompt to generate an AI-driven developer workflow.</p>
            <form onSubmit={handleSubmit}>
              <label htmlFor="requirement">Project requirement</label>
              <textarea
                id="requirement"
                rows="8"
                value={requirement}
                onChange={(event) => setRequirement(event.target.value)}
                placeholder="Build a team collaboration dashboard with authentication, analytics, and notifications."
              />
              <button type="submit">Generate project</button>
              {error && <div className="error-message">{error}</div>}
              {status && <div className="status-message">{status}</div>}
            </form>
          </motion.div>
        </section>

        {result && (
          <motion.section
            className="result-panel"
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.1 }}
          >
            <div className="result-grid">
              <Panel title="Tasks" content={result.tasks} />
              <Panel title="Review" content={result.review} />
              <Panel title="Tests" content={result.tests} />
              <CodePanel code={result.code} />
            </div>
          </motion.section>
        )}
      </motion.main>
    </div>
  )
}
      </motion.main>
    </div>
  )
}

function Panel({ title, content }) {
  return (
    <div className="panel">
      <div className="panel-heading">
        <span>{title}</span>
      </div>
      <div className="panel-body">
        <pre>{content || 'No content available.'}</pre>
      </div>
    </div>
  )
}

function CodePanel({ code }) {
  return (
    <div className="panel code-panel">
      <div className="panel-heading">
        <span>Generated Code</span>
      </div>
      <div className="panel-body code-body">
        <pre>{code || 'No code available.'}</pre>
      </div>
    </div>
  )
}

export default App
