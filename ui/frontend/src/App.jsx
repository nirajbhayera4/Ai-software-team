import { useEffect, useMemo, useState } from 'react'

const API_URL = typeof window !== 'undefined'
  ? `${window.location.protocol}//${window.location.hostname}:8000`
  : 'http://localhost:8000'

const emptyProject = {
  name: '',
  requirement: '',
}

function App() {
  const [token, setToken] = useState(() => localStorage.getItem('aiTeamToken') || '')
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem('aiTeamUser')
    try {
      return stored ? JSON.parse(stored) : null
    } catch {
      localStorage.removeItem('aiTeamUser')
      return null
    }
  })
  const [authMode, setAuthMode] = useState('login')
  const [authForm, setAuthForm] = useState({ username: 'admin', password: 'password' })
  const [projectForm, setProjectForm] = useState(emptyProject)
  const [projects, setProjects] = useState([])
  const [selectedProjectId, setSelectedProjectId] = useState(null)
  const [runs, setRuns] = useState([])
  const [activeRun, setActiveRun] = useState(null)
  const [activeTask, setActiveTask] = useState(null)
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')

  const selectedProject = useMemo(
    () => projects.find((project) => project.id === selectedProjectId),
    [projects, selectedProjectId],
  )

  async function request(path, options = {}) {
    const response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
      },
    })

    const data = await response.json()
    if (!response.ok) {
      if (response.status === 401) {
        logout()
      }
      throw new Error(data.detail || 'Request failed.')
    }
    return data
  }

  async function loadProjects() {
    if (!token) return
    const data = await request('/projects')
    setProjects(data.projects)
    if (data.projects.length === 0) {
      setSelectedProjectId(null)
      return
    }
    if (!selectedProjectId || !data.projects.some((project) => project.id === selectedProjectId)) {
      setSelectedProjectId(data.projects[0].id)
    }
  }

  async function loadRuns(projectId) {
    if (!projectId) return
    const data = await request(`/projects/${projectId}/runs`)
    setRuns(data.runs)
    if (data.runs.length > 0) {
      await loadRun(data.runs[0].id)
    } else {
      setActiveRun(null)
      setActiveTask(null)
    }
  }

  async function loadRun(runId) {
    const data = await request(`/runs/${runId}`)
    setActiveRun(data.run)
    const taskId = data.run?.final_output?.task_id
    if (taskId) {
      await loadTask(taskId)
    } else {
      setActiveTask(null)
    }
  }

  async function loadTask(taskId) {
    const data = await request(`/tasks/${taskId}`)
    setActiveTask(data.task)
  }

  useEffect(() => {
    loadProjects().catch((err) => setError(err.message))
  }, [token])

  useEffect(() => {
    if (!token) return

    request('/auth/session')
      .then((data) => {
        localStorage.setItem('aiTeamUser', JSON.stringify(data.user))
        setUser(data.user)
      })
      .catch((err) => setError(err.message))
  }, [token])

  useEffect(() => {
    loadRuns(selectedProjectId).catch((err) => setError(err.message))
  }, [selectedProjectId])

  async function handleAuth(event) {
    event.preventDefault()
    setError('')
    setStatus(authMode === 'login' ? 'Signing in...' : 'Creating account...')

    try {
      const data = await fetch(`${API_URL}/auth/${authMode === 'login' ? 'login' : 'register'}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(authForm),
      }).then(async (response) => {
        const body = await response.json()
        if (!response.ok) throw new Error(body.detail || 'Authentication failed.')
        return body
      })

      localStorage.setItem('aiTeamToken', data.access_token)
      localStorage.setItem('aiTeamUser', JSON.stringify(data.user))
      setToken(data.access_token)
      setUser(data.user)
      setStatus('')
    } catch (err) {
      setStatus('')
      setError(err.message)
    }
  }

  async function handleCreateProject(event) {
    event.preventDefault()
    setError('')
    setStatus('Creating project...')

    try {
      const data = await request('/projects', {
        method: 'POST',
        body: JSON.stringify(projectForm),
      })
      setProjectForm(emptyProject)
      await loadProjects()
      setSelectedProjectId(data.project.id)
      setStatus('Project created.')
    } catch (err) {
      setStatus('')
      setError(err.message)
    }
  }

  async function handleRunProject() {
    if (!selectedProject) return
    setError('')
    setStatus('Running manager, developer, reviewer, tester, and sandbox...')
    setActiveRun(null)
    setActiveTask(null)

    try {
      const data = await request(`/projects/${selectedProject.id}/runs`, { method: 'POST' })
      await loadProjects()
      await loadRuns(selectedProject.id)
      await loadRun(data.run_id)
      if (data.task_id) {
        await loadTask(data.task_id)
      }
      setStatus(`Run ${data.status}.`)
    } catch (err) {
      setStatus('')
      setError(err.message)
    }
  }

  function logout() {
    localStorage.removeItem('aiTeamToken')
    localStorage.removeItem('aiTeamUser')
    setToken('')
    setUser(null)
    setProjects([])
    setSelectedProjectId(null)
    setRuns([])
    setActiveRun(null)
    setActiveTask(null)
    setStatus('')
  }

  if (!token) {
    return (
      <main className="login-shell">
        <section className="login-panel">
          <p className="eyebrow">AI Software Team</p>
          <h1>{authMode === 'login' ? 'Project dashboard' : 'Create account'}</h1>
          <p className="muted">
            {authMode === 'login'
              ? 'Sign in to manage your projects, trigger agent runs, inspect outputs, and keep every run stored.'
              : 'Register to get a private project workspace tied to your user account.'}
          </p>
          <div className="auth-tabs" role="tablist" aria-label="Authentication mode">
            <button
              className={authMode === 'login' ? 'active' : ''}
              type="button"
              onClick={() => {
                setAuthMode('login')
                setError('')
                setStatus('')
              }}
            >
              Login
            </button>
            <button
              className={authMode === 'register' ? 'active' : ''}
              type="button"
              onClick={() => {
                setAuthMode('register')
                setError('')
                setStatus('')
              }}
            >
              Register
            </button>
          </div>
          <form onSubmit={handleAuth} className="stack">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              value={authForm.username}
              onChange={(event) => setAuthForm({ ...authForm, username: event.target.value })}
            />
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={authForm.password}
              onChange={(event) => setAuthForm({ ...authForm, password: event.target.value })}
            />
            <button type="submit">{authMode === 'login' ? 'Login' : 'Register'}</button>
          </form>
          {error && <p className="message error">{error}</p>}
          {status && <p className="message">{status}</p>}
        </section>
      </main>
    )
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Architecture dashboard</p>
          <h1>AI Software Team</h1>
        </div>
        <div className="user-area">
          <span>{user?.username}</span>
          <button className="secondary" type="button" onClick={logout}>Logout</button>
        </div>
      </header>

      <main className="dashboard">
        <aside className="sidebar">
          <section className="panel">
            <h2>New project</h2>
            <form onSubmit={handleCreateProject} className="stack">
              <label htmlFor="project-name">Name</label>
              <input
                id="project-name"
                value={projectForm.name}
                onChange={(event) => setProjectForm({ ...projectForm, name: event.target.value })}
                placeholder="Inventory API"
              />
              <label htmlFor="requirement">Requirement</label>
              <textarea
                id="requirement"
                value={projectForm.requirement}
                onChange={(event) => setProjectForm({ ...projectForm, requirement: event.target.value })}
                placeholder="Build a REST API with auth, products, orders, tests, and documentation."
              />
              <button type="submit">Create project</button>
            </form>
          </section>

          <section className="panel">
            <h2>Projects</h2>
            <div className="project-list">
              {projects.map((project) => (
                <button
                  className={project.id === selectedProjectId ? 'project-item active' : 'project-item'}
                  key={project.id}
                  type="button"
                  onClick={() => setSelectedProjectId(project.id)}
                >
                  <strong>{project.name}</strong>
                  <span>{project.latest_run_status || project.status}</span>
                </button>
              ))}
              {projects.length === 0 && <p className="muted">No projects yet.</p>}
            </div>
          </section>
        </aside>

        <section className="workspace">
          <section className="panel project-header">
            <div>
              <h2>{selectedProject?.name || 'Select a project'}</h2>
              <p className="muted">{selectedProject?.requirement || 'Create a project to start the agent workflow.'}</p>
            </div>
            <button type="button" disabled={!selectedProject} onClick={handleRunProject}>
              Run agents
            </button>
          </section>

          <section className="flow">
            {['Web UI', 'API Server', 'Agent Orchestrator', 'Execution Sandbox', 'Database'].map((step) => (
              <div className="flow-step" key={step}>{step}</div>
            ))}
          </section>

          {(status || error) && (
            <div className={error ? 'message error' : 'message'}>
              {error || status}
            </div>
          )}

          <section className="content-grid">
            <div className="panel">
              <h2>Runs</h2>
              <div className="run-list">
                {runs.map((run) => (
                  <button
                    className={activeRun?.id === run.id ? 'run-item active' : 'run-item'}
                    key={run.id}
                    type="button"
                    onClick={() => loadRun(run.id).catch((err) => setError(err.message))}
                  >
                    <span>Run #{run.id}</span>
                    <strong>{run.status}</strong>
                  </button>
                ))}
                {runs.length === 0 && <p className="muted">No runs yet.</p>}
              </div>
            </div>

            <div className="outputs">
              <Observability task={activeTask} />
              <Output title="Manager Tasks" value={activeRun?.final_output?.tasks} />
              <Output title="Developer Output" value={activeRun?.final_output?.implementation} code />
              <Output title="Reviewer Notes" value={activeRun?.final_output?.review} />
              <Output title="Tester Plan" value={activeRun?.final_output?.test_plan} />
              <Output
                title="Sandbox"
                value={activeRun?.final_output?.sandbox
                  ? `${activeRun.final_output.sandbox.status}\n${activeRun.final_output.sandbox.summary}\n${activeRun.final_output.sandbox.logs || ''}`
                  : ''}
              />
            </div>
          </section>
        </section>
      </main>
    </div>
  )
}

function formatDuration(milliseconds) {
  if (!milliseconds) return '0.0 sec'
  return `${(milliseconds / 1000).toFixed(1)} sec`
}

function formatCost(value) {
  const amount = Number(value || 0)
  return amount > 0 ? `$${amount.toFixed(6)}` : '$0.000000'
}

function statusMark(status) {
  if (status === 'completed' || status === 'passed') return '✓'
  if (status === 'failed') return '✗'
  return '•'
}

function Observability({ task }) {
  const agentRuns = task?.agent_runs || []
  const llmCalls = task?.llm_calls || []

  return (
    <section className="panel observability">
      <div className="section-heading">
        <h2>{task ? `Task #${task.id} observability` : 'Task observability'}</h2>
        <span>Total: {formatDuration(task?.total_duration_ms)}</span>
      </div>

      <div className="timeline">
        {agentRuns.map((run) => (
          <div className="timeline-row" key={run.id}>
            <span>{run.agent_name}</span>
            <strong className={run.status === 'failed' ? 'failed' : 'passed'}>
              {statusMark(run.status)}
            </strong>
            <span>{formatDuration(run.duration_ms)}</span>
          </div>
        ))}
        {agentRuns.length === 0 && <p className="muted">No agent runs recorded yet.</p>}
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Agent</th>
              <th>Model</th>
              <th>Input</th>
              <th>Output</th>
              <th>Latency</th>
              <th>Cost</th>
              <th>Status</th>
              <th>Error</th>
            </tr>
          </thead>
          <tbody>
            {llmCalls.map((call) => (
              <tr key={call.id}>
                <td>{call.agent_name}</td>
                <td>{call.model}</td>
                <td>{call.input_tokens}</td>
                <td>{call.output_tokens}</td>
                <td>{formatDuration(call.latency_ms)}</td>
                <td>{formatCost(call.cost_usd)}</td>
                <td>{call.status}</td>
                <td>{call.error || '-'}</td>
              </tr>
            ))}
            {llmCalls.length === 0 && (
              <tr>
                <td colSpan="8">No LLM calls recorded yet.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  )
}

function Output({ title, value, code = false }) {
  const renderedValue = typeof value === 'object' && value !== null
    ? JSON.stringify(value, null, 2)
    : value

  return (
    <section className={code ? 'panel output code-output' : 'panel output'}>
      <h2>{title}</h2>
      <pre>{renderedValue || 'No output yet.'}</pre>
    </section>
  )
}

export default App
