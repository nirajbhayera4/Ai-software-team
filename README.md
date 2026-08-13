# AI Software Team

AI Software Team is a starter workspace for experimenting with a multi-agent
software-development workflow. The project is organized around agent roles,
shared tools, prompts, a workflow graph, and a small UI entry point.

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
Compile/check generated code when enabled
        |
        v
SQLite Database
Projects / Runs / Agent outputs
```

The React dashboard stores an auth token locally after login, creates projects,
starts agent runs, and displays saved outputs. The API persists users, projects,
runs, and agent outputs in `data/ai_software_team.db`.

By default the sandbox records a skipped status. Set `SANDBOX_ENABLED=true` to
compile generated Python code during each run.

## Project Structure

```text
agents/      Role-specific agent implementations
graph/       Workflow orchestration
prompts/     Prompt templates used by agents
tools/       Shared integrations and helper functions
ui/          User interface entry point
db.py        SQLite persistence layer
api.py       Auth, project, run, and generation API
orchestrator.py Agent workflow manager
sandbox.py   Local execution sandbox checks
main.py      Application entry point
```

## Planned Agent Roles

- `manager`: breaks work into tasks and coordinates the workflow
- `developer`: implements requested changes
- `reviewer`: reviews code for correctness and maintainability
- `tester`: validates behavior and reports failures

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
```

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

## Run

```bash
python main.py
```

## React Frontend

A separate animated frontend is available at `ui/frontend`.

> Note: the frontend UI is currently under active development, including the landing page,
> login flow, and backend integration.

```bash
cd ui/frontend
npm install
npm run dev
```

The frontend calls the backend API at `http://localhost:8000`. Run the API with:

```bash
uvicorn api:app --reload --port 8000
```

Default development login:

```text
username: admin
password: password
```

## GitHub and push protection

If GitHub rejects a push because it detected a secret in history, remove the
secret from all commits before pushing again.

- Do not keep real API keys in tracked commits.
- Use `.env.example` for template values.
- If you need to push, generate a GitHub personal access token (PAT) and use it
  instead of a password.

## Status

This repository is currently under active development. The package layout and
frontend scaffold are in place, but the agent implementations, workflow logic,
backend API integration, tools, and UI are still being built and refined.

## Next Steps

- Define the workflow in `graph/workflow.py`
- Implement each agent in `agents/`
- Add prompt templates in `prompts/`
- Add file and GitHub helpers in `tools/`
- Build the UI in `ui/app.py`
