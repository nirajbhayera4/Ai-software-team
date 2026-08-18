import { useEffect, useMemo, useState } from 'react'

const API_URL = typeof window !== 'undefined'
  ? `${window.location.protocol}//${window.location.hostname}:8000`
  : 'http://localhost:8000'

const emptyProject = {
  name: '',
  requirement: '',
}

function formatRequestError(error) {
  if (error instanceof TypeError) {
    return `Could not reach the API at ${API_URL}. Start the backend and make sure CORS allows this frontend origin.`
  }
  return error.message || 'Request failed.'
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
  const [benchmarks, setBenchmarks] = useState([])
  const [activeBenchmark, setActiveBenchmark] = useState(null)
  const [benchmarkLimit, setBenchmarkLimit] = useState('3')
  const [activeView, setActiveView] = useState('dashboard')
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

    const data = await response.json().catch(() => ({}))
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

  async function loadBenchmarks() {
    if (!token) return
    const data = await request('/benchmarks')
    setBenchmarks(data.benchmarks)
    if (data.benchmarks.length > 0 && !activeBenchmark) {
      await loadBenchmark(data.benchmarks[0].id)
    }
  }

  async function loadBenchmark(benchmarkId) {
    const data = await request(`/benchmarks/runs/${benchmarkId}`)
    setActiveBenchmark({ ...data.benchmark, summary: data.summary })
  }

  useEffect(() => {
    loadProjects().catch((err) => setError(formatRequestError(err)))
    loadBenchmarks().catch((err) => setError(formatRequestError(err)))
  }, [token])

  useEffect(() => {
    if (!token) return

    request('/auth/session')
      .then((data) => {
        localStorage.setItem('aiTeamUser', JSON.stringify(data.user))
        setUser(data.user)
      })
      .catch((err) => setError(formatRequestError(err)))
  }, [token])

  useEffect(() => {
    loadRuns(selectedProjectId).catch((err) => setError(formatRequestError(err)))
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
        const body = await response.json().catch(() => ({}))
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
      setError(formatRequestError(err))
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
      setError(formatRequestError(err))
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
      setError(formatRequestError(err))
    }
  }

  async function handleRunBenchmark(event) {
    event.preventDefault()
    setError('')
    setStatus('Running benchmark...')

    const parsedLimit = Number.parseInt(benchmarkLimit, 10)
    const limit = Number.isFinite(parsedLimit) && parsedLimit > 0 ? parsedLimit : null
    try {
      const data = await request('/benchmarks/runs', {
        method: 'POST',
        body: JSON.stringify({ limit }),
      })
      await loadBenchmarks()
      await loadBenchmark(data.benchmark.id)
      setStatus(`Benchmark ${data.summary.tasks_completed} completed.`)
    } catch (err) {
      setStatus('')
      setError(formatRequestError(err))
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
    setBenchmarks([])
    setActiveBenchmark(null)
    setActiveView('dashboard')
    setStatus('')
  }

  const finalOutput = activeRun?.final_output || {}
  const implementation = finalOutput.implementation || {}
  const review = finalOutput.review || {}
  const testPlan = finalOutput.test_plan || {}
  const sandbox = finalOutput.sandbox || {}
  const workflowErrors = finalOutput.workflow_errors || []
  const filesChanged = implementation.files_changed || activeTask?.file_changes || []
  const agentRuns = activeTask?.agent_runs || []
  const latestRunStatus = activeRun?.status || selectedProject?.latest_task_status || selectedProject?.status || 'idle'
  const navItems = [
    ['dashboard', 'Dashboard'],
    ['agents', 'Agents'],
    ['runs', 'Runs'],
    ['evaluations', 'Evaluations'],
    ['settings', 'Settings'],
  ]

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
    <div className="product-shell">
      <aside className="app-nav">
        <div className="brand-block">
          <p className="eyebrow">AI Software Team</p>
          <strong>Workspace</strong>
        </div>

        <nav className="nav-list" aria-label="Main navigation">
          {navItems.map(([id, label]) => (
            <button
              className={activeView === id ? 'nav-item active' : 'nav-item'}
              key={id}
              type="button"
              onClick={() => setActiveView(id)}
            >
              {label}
            </button>
          ))}
        </nav>

        <section className="nav-section">
          <div className="nav-heading">
            <span>Projects</span>
            <strong>{projects.length}</strong>
          </div>
          <div className="project-list compact">
            {projects.map((project) => (
              <button
                className={project.id === selectedProjectId ? 'project-item active' : 'project-item'}
                key={project.id}
                type="button"
                onClick={() => {
                  setSelectedProjectId(project.id)
                  setActiveView('dashboard')
                }}
              >
                <strong>{project.name}</strong>
                <span>{project.latest_task_status || project.status}</span>
              </button>
            ))}
            {projects.length === 0 && <p className="muted">No projects yet.</p>}
          </div>
        </section>

        <div className="nav-footer">
          <span>{user?.username}</span>
          <button className="secondary" type="button" onClick={logout}>Logout</button>
        </div>
      </aside>

      <main className="main-stage">
        <header className="workspace-header">
          <div>
            <p className="eyebrow">{activeView}</p>
            <h1>{selectedProject?.name || 'Create your first project'}</h1>
            <p className="muted">{selectedProject?.requirement || 'Start with a requirement, then run the AI team workflow.'}</p>
          </div>
          <div className="header-actions">
            <span className={`status-pill ${latestRunStatus}`}>{latestRunStatus}</span>
            <button type="button" disabled={!selectedProject} onClick={handleRunProject}>
              Run agents
            </button>
          </div>
        </header>

        {(status || error) && (
          <div className={error ? 'message error' : 'message'}>
            {error || status}
          </div>
        )}

        {activeView === 'dashboard' && (
          <section className="dashboard-view">
            <section className="panel task-brief">
              <div>
                <p className="eyebrow">Task</p>
                <h2>{activeTask?.title || 'Initial requirement'}</h2>
                <p className="muted">{activeTask?.requirement || selectedProject?.requirement || 'No task selected.'}</p>
              </div>
              <div className="summary-strip">
                <SummaryStat label="Agents" value={agentRuns.length} />
                <SummaryStat label="Duration" value={formatDuration(activeTask?.total_duration_ms)} />
                <SummaryStat label="Files" value={filesChanged.length} />
                <SummaryStat label="Errors" value={workflowErrors.length} />
              </div>
            </section>

            <section className="primary-grid">
              <AgentTimeline task={activeTask} />
              <section className="panel">
                <div className="section-heading">
                  <h2>Runs</h2>
                  <span>{runs.length}</span>
                </div>
                <div className="run-list">
                  {runs.map((run) => (
                    <button
                      className={activeRun?.id === run.id ? 'run-item active' : 'run-item'}
                      key={run.id}
                      type="button"
                      onClick={() => loadRun(run.id).catch((err) => setError(formatRequestError(err)))}
                    >
                      <span>Run #{run.id}</span>
                      <strong>{run.status}</strong>
                    </button>
                  ))}
                  {runs.length === 0 && <p className="muted">No runs yet.</p>}
                </div>
              </section>
            </section>

            <section className="detail-grid">
              <FilesChanged files={filesChanged} />
              <TestsPanel testPlan={testPlan} sandbox={sandbox} />
              <ReviewPanel review={review} />
            </section>
          </section>
        )}

        {activeView === 'agents' && (
          <section className="stacked-view">
            <AgentTimeline task={activeTask} expanded />
            <Observability task={activeTask} />
          </section>
        )}

        {activeView === 'runs' && (
          <section className="runs-view">
            <section className="panel">
              <h2>Run history</h2>
              <div className="run-list wide">
                {runs.map((run) => (
                  <button
                    className={activeRun?.id === run.id ? 'run-item active' : 'run-item'}
                    key={run.id}
                    type="button"
                    onClick={() => loadRun(run.id).catch((err) => setError(formatRequestError(err)))}
                  >
                    <span>Run #{run.id}</span>
                    <strong>{run.status}</strong>
                  </button>
                ))}
                {runs.length === 0 && <p className="muted">No runs yet.</p>}
              </div>
            </section>
            <Output title="Manager Tasks" value={finalOutput.tasks} />
            <Output title="Developer Output" value={implementation} code />
            <Output title="Sandbox" value={sandbox} />
          </section>
        )}

        {activeView === 'evaluations' && (
          <section className="stacked-view">
            <section className="panel evaluation-runner">
              <div>
                <h2>Benchmark runner</h2>
                <p className="muted">Run a sample or full benchmark against the current AI workflow.</p>
              </div>
              <form onSubmit={handleRunBenchmark} className="benchmark-form horizontal">
                <label htmlFor="benchmark-limit-main">Tasks</label>
                <input
                  id="benchmark-limit-main"
                  min="1"
                  max="20"
                  type="number"
                  value={benchmarkLimit}
                  onChange={(event) => setBenchmarkLimit(event.target.value)}
                />
                <button type="submit">Run benchmark</button>
              </form>
            </section>
            <BenchmarkSummary benchmark={activeBenchmark} />
          </section>
        )}

        {activeView === 'settings' && (
          <section className="settings-grid">
            <section className="panel">
              <h2>New project</h2>
              <form onSubmit={handleCreateProject} className="stack">
                <label htmlFor="project-name">Name</label>
                <input
                  id="project-name"
                  value={projectForm.name}
                  onChange={(event) => setProjectForm({ ...projectForm, name: event.target.value })}
                  placeholder="E-Commerce"
                />
                <label htmlFor="requirement">Requirement</label>
                <textarea
                  id="requirement"
                  value={projectForm.requirement}
                  onChange={(event) => setProjectForm({ ...projectForm, requirement: event.target.value })}
                  placeholder="Build authentication, product catalog, cart, checkout, tests, and deployment notes."
                />
                <button type="submit">Create project</button>
              </form>
            </section>
            <section className="panel">
              <h2>Environment</h2>
              <dl className="settings-list">
                <div><dt>API</dt><dd>{API_URL}</dd></div>
                <div><dt>Session</dt><dd>{user?.username}</dd></div>
                <div><dt>Projects</dt><dd>{projects.length}</dd></div>
                <div><dt>Benchmarks</dt><dd>{benchmarks.length}</dd></div>
              </dl>
            </section>
          </section>
        )}
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
  if (status === 'completed' || status === 'passed') return 'OK'
  if (status === 'failed') return 'FAIL'
  return '...'
}

function formatPercent(value) {
  return `${(Number(value || 0) * 100).toFixed(1)}%`
}

function SummaryStat({ label, value }) {
  return (
    <div className="summary-stat">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function AgentTimeline({ task, expanded = false }) {
  const agentRuns = task?.agent_runs || []
  const expectedAgents = ['manager', 'developer', 'tester', 'reviewer', 'execution_sandbox']
  const displayedRuns = agentRuns.length > 0
    ? agentRuns
    : expectedAgents.map((agent) => ({ id: agent, agent_name: agent, status: 'idle', duration_ms: 0 }))

  return (
    <section className={expanded ? 'panel agent-timeline expanded' : 'panel agent-timeline'}>
      <div className="section-heading">
        <h2>Agent execution timeline</h2>
        <span>Total: {formatDuration(task?.total_duration_ms)}</span>
      </div>
      <div className="agent-steps">
        {displayedRuns.map((run) => (
          <div className="agent-step" key={run.id}>
            <div>
              <strong>{run.agent_name}</strong>
              <span>{run.status}</span>
            </div>
            <b className={run.status === 'failed' ? 'failed' : run.status === 'idle' ? 'idle' : 'passed'}>
              {statusMark(run.status)}
            </b>
            <small>{formatDuration(run.duration_ms)}</small>
          </div>
        ))}
      </div>
    </section>
  )
}

function FilesChanged({ files }) {
  return (
    <section className="panel detail-panel">
      <div className="section-heading">
        <h2>Files changed</h2>
        <span>{files.length}</span>
      </div>
      <div className="file-list">
        {files.map((file, index) => (
          <div className="file-row" key={`${file.path || file}-${index}`}>
            <strong>{file.path || file}</strong>
            <span>{file.change_summary || file.summary || file.purpose || 'Generated change'}</span>
          </div>
        ))}
        {files.length === 0 && <p className="muted">No file changes recorded.</p>}
      </div>
    </section>
  )
}

function TestsPanel({ testPlan, sandbox }) {
  return (
    <section className="panel detail-panel">
      <div className="section-heading">
        <h2>Tests</h2>
        <span>{sandbox?.status || 'idle'}</span>
      </div>
      <pre>{testPlan && Object.keys(testPlan).length ? JSON.stringify(testPlan, null, 2) : 'No test plan yet.'}</pre>
      {sandbox?.summary && <p className="muted">{sandbox.summary}</p>}
    </section>
  )
}

function ReviewPanel({ review }) {
  const issues = review?.issues || []

  return (
    <section className="panel detail-panel">
      <div className="section-heading">
        <h2>Review</h2>
        <span>{review?.approved ? 'approved' : 'pending'}</span>
      </div>
      <div className="review-score">
        <strong>{review?.overall_rating ?? '-'}</strong>
        <span>overall rating</span>
      </div>
      <div className="file-list">
        {issues.map((issue, index) => (
          <div className="file-row" key={`${issue.description || 'issue'}-${index}`}>
            <strong>{issue.severity || 'issue'}</strong>
            <span>{issue.description || issue.suggestion || 'Review issue recorded.'}</span>
          </div>
        ))}
        {issues.length === 0 && <p className="muted">No review issues recorded.</p>}
      </div>
    </section>
  )
}

function BenchmarkSummary({ benchmark }) {
  if (!benchmark) {
    return (
      <section className="panel benchmark-summary">
        <h2>Evaluation</h2>
        <p className="muted">Run a benchmark to measure completion, tests, review approval, latency, and cost.</p>
      </section>
    )
  }

  const metrics = [
    ['Tasks completed', `${benchmark.completed_tasks}/${benchmark.total_tasks}`],
    ['Tests passing', formatPercent(benchmark.tests_passing_rate)],
    ['Reviewer approval', formatPercent(benchmark.reviewer_approval_rate)],
    ['Average iterations', Number(benchmark.average_iterations || 0).toFixed(2)],
    ['Average latency', formatDuration(benchmark.average_latency_ms)],
    ['Average LLM cost', formatCost(benchmark.average_cost_usd)],
    ['Correctness score', Number(benchmark.average_correctness_score || 0).toFixed(3)],
  ]

  return (
    <section className="panel benchmark-summary">
      <div className="section-heading">
        <h2>Evaluation #{benchmark.id}</h2>
        <span>{benchmark.status}</span>
      </div>
      <div className="metric-grid">
        {metrics.map(([label, value]) => (
          <div className="metric" key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Task</th>
              <th>Status</th>
              <th>Score</th>
              <th>Tests</th>
              <th>Review</th>
              <th>Latency</th>
              <th>Cost</th>
            </tr>
          </thead>
          <tbody>
            {(benchmark.results || []).map((result) => (
              <tr key={result.id}>
                <td>{result.name}</td>
                <td>{result.status}</td>
                <td>{Number(result.correctness_score || 0).toFixed(3)}</td>
                <td>{result.tests_passed ? 'passed' : 'failed'}</td>
                <td>{result.reviewer_approved ? 'approved' : 'rejected'}</td>
                <td>{formatDuration(result.latency_ms)}</td>
                <td>{formatCost(result.cost_usd)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
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
