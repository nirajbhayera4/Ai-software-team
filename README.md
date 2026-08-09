# AI Software Team

AI Software Team is a starter workspace for experimenting with a multi-agent
software-development workflow. The project is organized around agent roles,
shared tools, prompts, a workflow graph, and a small UI entry point.

## Project Structure

```text
agents/      Role-specific agent implementations
graph/       Workflow orchestration
prompts/     Prompt templates used by agents
tools/       Shared integrations and helper functions
ui/          User interface entry point
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

## GitHub and push protection

If GitHub rejects a push because it detected a secret in history, remove the
secret from all commits before pushing again.

- Do not keep real API keys in tracked commits.
- Use `.env.example` for template values.
- If you need to push, generate a GitHub personal access token (PAT) and use it
  instead of a password.

## Status

This repository is currently a scaffold. The package layout is in place, but the
agent implementations, workflow logic, tools, and UI still need to be built.

## Next Steps

- Define the workflow in `graph/workflow.py`
- Implement each agent in `agents/`
- Add prompt templates in `prompts/`
- Add file and GitHub helpers in `tools/`
- Build the UI in `ui/app.py`
