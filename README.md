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

Create and activate a virtual environment:

```bash
python -m venv venv
venv\Scripts\activate
```

Install dependencies once they are added to `requirements.txt`:

```bash
pip install -r requirements.txt
```

Run the project:

```bash
python main.py
```

## Status

This repository is currently a scaffold. The package layout is in place, but the
agent implementations, workflow logic, tools, and UI still need to be built.

## Next Steps

- Define the workflow in `graph/workflow.py`
- Implement each agent in `agents/`
- Add prompt templates in `prompts/`
- Add file and GitHub helpers in `tools/`
- Build the UI in `ui/app.py`
