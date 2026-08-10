import { useState } from 'react'
import { motion } from 'framer-motion'

const API_URL = typeof window !== 'undefined'
  ? `${window.location.protocol}//${window.location.hostname}:8000`
  : 'http://localhost:8000'

function App() {
  const [requirement, setRequirement] = useState('')
  const [result, setResult] = useState(null)
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const [showLanding, setShowLanding] = useState(true)
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
      setShowLanding(false)
      setUsername('')
      setPassword('')
      setLoginError('')
      return
    }

    setLoginError('Invalid credentials. Use admin / password.')
  }

  const showLoginPage = !showLanding && !loggedIn

  if (showLanding) {
    return (
      <div className="landing-page">
        <header className="landing-header">
          <div className="landing-brand">
            <span className="badge">AI Software Team</span>
            <strong>Intelligent software delivery for modern teams.</strong>
          </div>
          <nav className="landing-nav">
            <a href="#how-it-works">How it works</a>
            <a href="#benefits">Why it helps</a>
            <a href="#made-with">Built with</a>
            <button className="nav-button" onClick={() => setShowLanding(false)}>
              Get started
            </button>
          </nav>
        </header>

        <section className="landing-hero">
          <div>
            <p className="eyebrow">AI-driven software development</p>
            <h1>From requirement to reviewed code — powered by a collaborative AI team.</h1>
            <p>
              This app models modern software development with manager, developer,
              reviewer, and tester roles. It guides your idea into tasks, code,
              feedback and tests in a single workflow.
            </p>
            <div className="hero-actions">
              <button onClick={() => setShowLanding(false)}>Start with login</button>
              <a href="#benefits">Explore benefits</a>
            </div>
          </div>
          <div className="hero-visual-large">
            <div className="visual-card large">
              <div className="visual-dot top" />
              <div className="visual-line" />
              <div className="visual-dot middle" />
              <div className="visual-line" />
              <div className="visual-dot bottom" />
            </div>
          </div>
        </section>

        <section id="how-it-works" className="landing-section">
          <div className="section-content">
            <h2>How it works</h2>
            <p>
              The workflow starts with a product requirement, then the AI manager defines
              tasks, the AI developer writes code, the AI reviewer checks quality, and the
              AI tester creates validation plans.
            </p>
          </div>
          <div className="section-grid">
            <div className="feature-card">
              <h3>Manager-driven planning</h3>
              <p>Create structured work items from a single prompt.</p>
            </div>
            <div className="feature-card">
              <h3>Developer generation</h3>
              <p>Produce implementation code with clear intent and style.</p>
            </div>
            <div className="feature-card">
              <h3>Review & testing</h3>
              <p>Receive feedback and test guidance automatically.</p>
            </div>
          </div>
        </section>

        <section id="benefits" className="landing-section alternate">
          <div className="section-content wide">
            <h2>Why this matters for software development</h2>
            <p>
              Using an AI team helps reduce rework, improve code quality, and make
              planning faster. It connects requirements, implementation, review,
              and validation in one experience.
            </p>
          </div>
          <div className="benefits-grid">
            <div>
              <h4>Faster discovery</h4>
              <p>Turn ideas into actionable tasks in seconds.</p>
            </div>
            <div>
              <h4>Better alignment</h4>
              <p>Keep requirements, code, and tests in sync.</p>
            </div>
            <div>
              <h4>Less manual handoff</h4>
              <p>Reduce context switching between roles and tools.</p>
            </div>
          </div>
        </section>

        <section id="made-with" className="landing-section">
          <div className="section-content">
            <h2>Built with modern AI design</h2>
            <p>
              This app combines a lightweight backend API with a reactive frontend to
              deliver a smooth, animated workflow experience.
            </p>
          </div>
          <div className="made-grid">
            <div className="made-card">
              <strong>React + Vite</strong>
              <p>Fast frontend rendering and fluid animations.</p>
            </div>
            <div className="made-card">
              <strong>FastAPI</strong>
              <p>API gateway for task and code generation requests.</p>
            </div>
            <div className="made-card">
              <strong>AI workflow</strong>
              <p>Layered generation with planning, implementation, review, and tests.</p>
            </div>
          </div>
        </section>

        <footer className="landing-footer">
          <div className="footer-copy">
            <p>Ready to experience software planning with AI? Login to continue.</p>
            <p className="footer-credit">
              Built by NIRAJ BHAYERA — AI Software Team prototype.
              <span>Contact: <a href="mailto:nirajbhayera4@gmail.com">nirajbhayera4@gmail.com</a> | <a href="https://github.com/nirajbhayera4" target="_blank" rel="noreferrer">github.com/nirajbhayera4</a></span>
            </p>
          </div>
          <button onClick={() => setShowLanding(false)}>Login now</button>
        </footer>
      </div>
    )
  }

  if (showLoginPage) {
    return (
      <div className="page-shell login-page">
        <motion.header
          initial={{ y: -80, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          className="login-hero"
        >
          <div className="login-copy">
            <span className="badge">Secure access</span>
            <h1>Login to continue</h1>
            <p>
              Enter your credentials to access the AI workflow generator and move from
              idea to implementation with confidence.
            </p>
          </div>
        </motion.header>

        <main className="content">
          <section className="form-panel login-panel">
            <motion.div
              className="form-card login-card"
              initial={{ scale: 0.98, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.6 }}
            >
              <div className="login-header">
                <span className="badge">Welcome back</span>
                <h1>Sign in to your workspace</h1>
                <p>
                  Use the sample credentials to proceed: admin / password. This is a
                  placeholder login for the current prototype.
                </p>
              </div>
              <form className="login-form" onSubmit={handleLogin}>
                <label htmlFor="username">Username</label>
                <input
                  id="username"
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
              <div className="login-actions">
                <button type="button" className="secondary" onClick={() => setShowLanding(true)}>
                  Back to landing
                </button>
              </div>
            </motion.div>
          </section>
        </main>
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
