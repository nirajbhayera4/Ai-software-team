#agents/developer.py

from langchain_core.messages import HumanMessage

from agents.llm import invoke_agent_llm
from agents.structured_output import json_prompt_schema, parse_json_response

def developer(state):
    """
    Developer agent 

    Input :
    state["requirement"]
    state["tasks"]

    output: state["implementation"]
    """


    requirement=state["requirement"]
    tasks=state["tasks"]
    schema = {
        "task": "Implement login API",
        "files_changed": [
            {
                "path": "src/auth/login.py",
                "purpose": "Login endpoint implementation",
            }
        ],
        "changes": "Concise implementation summary",
        "code": "Generated code or multi-file code listing",
        "dependencies": [
            "pytest==8.3.4",
        ],
        "test_code": "Optional executable Python test code for the sandbox.",
        "tests_required": [
            "valid login",
            "invalid password",
            "missing email",
        ],
        "assumptions": ["Important implementation assumption"],
    }
    prompt=f"""
You are a Expert senior software Engineer
Your job is to implemen the project based on the manager's plan.

PROJECT REQUIREMENT:
{requirement}

TASKS:
{tasks}

Instructions:
1. Write clean , modular python code.
2. Use obejct oriented programming whenever appropriate.
3.Add the comments where neccessary.
4. Follow the PEP8 style guide.
5. Include proper error handling.
6. If multiple files are needed, sepearate them using:
===================
filename.py
===================
7.Explain then folder structure if necessary.
8.Return valid JSON only.
9.Use exactly this JSON shape:
{json_prompt_schema(schema)}
10. Put third-party Python packages needed to run the code in dependencies.
11. Put executable Python tests in test_code when possible. Use only Python code, not prose.

"""
    response = invoke_agent_llm(
        "developer",
        [
            HumanMessage(content=prompt)
        ],
        temperature=0.2,
        task_id=state.get("task", {}).get("id"),
        agent_run_id=state.get("current_agent_run_id"),
    )
    fallback = {
        "task": "Implement project requirement",
        "files_changed": [],
        "changes": "The developer returned unstructured code text.",
        "code": response.content,
        "dependencies": [],
        "test_code": "",
        "tests_required": [],
        "assumptions": [],
    }
    return {"implementation": parse_json_response(response.content, fallback)}
