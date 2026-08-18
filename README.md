# AI Software Team

AI Software Team is a full-stack multi-agent software-development dashboard. It
lets authenticated users create private projects, run a manager/developer/reviewer/tester
workflow, inspect generated outputs, and review execution/LLM observability for
each task.

## Current Architecture

```text
Web UI Project Dashboard
        |
        v
FastAPI Server
Auth / Projects / Runs API
        |
        v
Agent Orchestrator
Manager -> Developer -> Reviewer -> Tester
        |
        v
Execution Sandbox
Containerized generated-code checks
        |
        v
SQLAlchemy Database
Users / Projects / Tasks / Agent runs / LLM calls
```

The React dashboard supports register, login, logout, session restore, project
creation, run execution, output inspection, and observability views. The API
requires bearer-token authentication for project/task/run data and always checks
project ownership on the backend before returning or mutating project-scoped
resources.

The API persists users, projects, runs, tasks, agent messages, file changes, test
runs, reviews, LLM calls, and agent outputs through SQLAlchemy models. Local
development defaults to SQLite at `data/ai_software_team.db`; production should
set `DATABASE_URL` to PostgreSQL.

Agent outputs are structured JSON objects instead of plain text blobs. The
manager returns task objects, the developer returns changed files/code/test
requirements, the reviewer returns scored findings, and the tester returns a
categorized test plan.

Each task stores an observability timeline for agent runs and LLM calls. The
dashboard shows per-agent duration, total task duration, model, input tokens,
output tokens, latency, estimated cost, status, and errors.

LLM calls are retried with configurable timeout and exponential backoff. Failed
attempts are recorded as `retrying`/`failed` observability rows. If an agent still
fails after retries, the workflow saves a structured fallback/error output and
continues where possible instead of crashing the whole run. Sandbox/test failure
and reviewer rejection mark the final workflow status as failed.

By default the sandbox records a skipped status. Set `SANDBOX_ENABLED=true` to
run generated Python code checks in a short-lived Docker container. When enabled,
the app refuses to execute generated code on the API server if Docker is not
available.

## Project Structure

```text
agents/      Role-specific agent implementations
graph/       Workflow orchestration
prompts/     Prompt templates used by agents
tools/       Shared integrations and helper functions
ui/          Streamlit entry point and React frontend
db.py        SQLAlchemy persistence layer
api.py       Auth, project, run, and generation API
orchestrator.py Agent workflow manager
sandbox.py   Containerized execution sandbox checks
main.py      Application entry point
```

## Core Features

- Authentication: register, login, logout, bearer-token sessions, and `/auth/session`.
- User-owned projects: users only see their own projects, and project/task/run IDs are rechecked on the backend.
- SQLAlchemy persistence: production-ready ORM layer with PostgreSQL support via `DATABASE_URL`.
- Multi-agent workflow: manager, developer, reviewer, tester, and execution sandbox.
- Container sandbox: generated Python code runs only in a short-lived Docker container when sandboxing is enabled.
- Observability: agent timeline, durations, total task time, LLM tokens, latency, estimated cost, status, and errors.
- Evaluation: 20 predefined coding benchmark tasks with completion, tests, review, iteration, latency, cost, and correctness metrics.
- Failure handling: LLM retries, timeout handling, malformed-output fallback, agent fallback outputs, sandbox/test failure, and reviewer rejection.

## Agent Roles

- `manager`: breaks work into tasks and coordinates the workflow
- `developer`: generates implementation output, optional dependencies, and optional executable tests
- `reviewer`: reviews code for correctness and maintainability
- `tester`: validates behavior and reports failures
- `execution_sandbox`: compiles/tests generated code in an isolated container

## Getting Started

Create and activate a virtual environment.

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

### Windows

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

This project uses a `.env` file for secrets and provider configuration.
Copy `.env.example` to `.env` and fill in your own values.

> The repository already ignores `.env` via `.gitignore`. Do not commit real API
> keys or credentials to source control.

Example for OpenAI:

```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4.1-mini
LLM_API_KEY=your-openai-api-key
LLM_INPUT_COST_PER_1M_TOKENS=0
LLM_OUTPUT_COST_PER_1M_TOKENS=0
LLM_TIMEOUT_SECONDS=60
LLM_MAX_RETRIES=2
LLM_RETRY_BASE_DELAY_SECONDS=1
```

Set the token cost values for your selected model/provider to enable estimated
LLM cost tracking. They default to `0` so pricing is not silently hard-coded.
Retries default to two attempts after the first failure. Each failed attempt is
stored in the `llm_calls` table and shown in the dashboard.

Example for OpenAI-compatible APIs:

```env
LLM_PROVIDER=openai-compatible
LLM_BASE_URL=https://provider.example.com/openai/v1
LLM_MODEL=provider-model-name
LLM_API_KEY=your-provider-api-key
```

Example for local Ollama:

```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.1
```

Database configuration:

```env
# Local default if omitted:
DATABASE_URL=sqlite:///data/ai_software_team.db

# Production example:
DATABASE_URL=postgresql+psycopg://user:password@host:5432/ai_software_team
```

Sandbox configuration:

```env
# Requires Docker. Runs generated code in an isolated container, not the API host.
SANDBOX_ENABLED=true
SANDBOX_DOCKER_IMAGE=python:3.12-slim
SANDBOX_TIMEOUT_SECONDS=30
SANDBOX_MEMORY=256m
SANDBOX_CPUS=1
SANDBOX_PIDS_LIMIT=128

# Keep false for strict isolation. Set true only if dependency installation must
# reach package indexes from inside the disposable container.
SANDBOX_ALLOW_NETWORK=false
```

Authentication configuration:

```env
APP_SECRET_KEY=replace-with-a-long-random-secret
APP_ADMIN_USERNAME=admin
APP_ADMIN_PASSWORD=password
```

The default admin credentials are for local development only. Set a strong
`APP_SECRET_KEY` and admin password outside local demos.

## Run

Run the FastAPI backend:

```bash
uvicorn api:app --reload --port 8000
```

Run the React frontend:

```bash
cd ui/frontend
npm install
npm run dev
```

The frontend calls the backend API at `http://localhost:8000` and runs at
`http://localhost:5173` by default.

You can also run the legacy entry point:

```bash
python main.py
```

Default development login:

```text
username: admin
password: password
```

Run the coding benchmark from the CLI:

```bash
python evaluation.py --owner-id 1 --limit 3
```

Omit `--limit` to run all 20 predefined benchmark tasks.

## API Overview

- `POST /auth/register`: create a user and return a bearer token.
- `POST /auth/login`: authenticate and return a bearer token.
- `GET /auth/session`: return the current authenticated user.
- `GET /projects`: list only the current user's projects.
- `POST /projects`: create a project owned by the current user.
- `GET /projects/{project_id}/tasks`: list tasks after ownership verification.
- `POST /projects/{project_id}/tasks`: create a project task after ownership verification.
- `GET /tasks/{task_id}`: return task workspace, agent runs, agent messages, outputs, and observability.
- `POST /tasks/{task_id}/runs`: run the workflow for a task after ownership verification.
- `POST /projects/{project_id}/runs`: run the full workflow for a project after ownership verification.
- `GET /projects/{project_id}/runs`: list project runs after ownership verification.
- `GET /runs/{run_id}`: return run outputs after ownership verification.
- `GET /benchmarks/tasks`: list predefined benchmark tasks.
- `GET /benchmarks`: list benchmark runs owned by the current user.
- `POST /benchmarks/runs`: run the benchmark for the current user.
- `GET /benchmarks/runs/{benchmark_run_id}`: return aggregate and per-task benchmark results.

## Database Tables

- `users`
- `projects`
- `tasks`
- `agent_runs`
- `agent_messages`
- `llm_calls`
- `file_changes`
- `test_runs`
- `reviews`
- `runs`
- `agents`
- `agent_outputs`
- `benchmark_runs`
- `benchmark_results`

## Sandbox Behavior

When `SANDBOX_ENABLED=false`, generated-code execution is skipped. When
`SANDBOX_ENABLED=true`, generated code is copied into a temporary workspace and
executed inside Docker with:

- no network by default
- CPU, memory, PID, and timeout limits
- read-only container filesystem
- dropped Linux capabilities
- `no-new-privileges`
- disposable workspace cleanup after execution

If Docker is unavailable while sandboxing is enabled, the app refuses to execute
generated code on the API server and records a failed sandbox result.

## Observability And Failure Handling

Each task workspace includes:

- `agent_runs`: ordered timeline with agent name, status, start/end time, and duration
- `llm_calls`: model, input tokens, output tokens, latency, estimated cost, status, and error
- `total_duration_ms`: total recorded agent-run duration
- `workflow_errors`: structured fallback, retry, reviewer rejection, sandbox, or test failure information

LLM failures are retried with exponential backoff. Timeouts, rate limits, API
unavailability, malformed model output, agent exceptions, sandbox failures, test
failures, and reviewer rejection are all captured as structured errors instead
of crashing the entire workflow.

## Evaluation

The benchmark harness runs predefined coding tasks through the same production
workflow and stores both per-task and aggregate measurements. Each benchmark run
tracks:

- tasks completed
- tests passing rate
- reviewer approval rate
- average iterations
- average latency
- average LLM cost
- average correctness score

Per-task benchmark rows link back to the created project/task when available, so
you can inspect the exact agent timeline, LLM calls, sandbox result, reviewer
output, and workflow errors behind each score.

## CI/CD

GitHub Actions workflows live in `.github/workflows`:

- `lint.yml`: runs Python lint/syntax checks and validates the frontend build graph.
- `test.yml`: runs unit checks, FastAPI integration checks, frontend build, Bandit, `pip-audit`, and `npm audit`.
- `deploy.yml`: runs after the `Test` workflow succeeds on `main`/`master`, or manually through `workflow_dispatch`.

The deploy workflow is disabled by default so a fresh repository does not fail
without production infrastructure. To enable deployment, set repository variable
`DEPLOY_ENABLED=true` and repository secret `DEPLOY_COMMAND` to the command your
deployment target requires.

## GitHub and push protection

If GitHub rejects a push because it detected a secret in history, remove the
secret from all commits before pushing again.

- Do not keep real API keys in tracked commits.
- Use `.env.example` for template values.
- If you need to push, generate a GitHub personal access token (PAT) and use it
  instead of a password.

## Status

The project now has the core production-facing pieces in place: authenticated
user workspaces, ORM-backed persistence, containerized execution checks,
observability, retry logic, and structured failure handling. It is still a
portfolio/development system, so use real secrets, a managed PostgreSQL
database, Docker sandbox capacity, and production deployment hardening before
running it for untrusted users.
