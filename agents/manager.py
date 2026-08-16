from langchain_core.messages import HumanMessage

from agents.llm import invoke_agent_llm
from agents.structured_output import json_prompt_schema, parse_json_response

def manager(state):
    """
    Manager agent 
    Input : state["requirement"]
    
    output: state["tasks"]
    """
    requirement=state["requirement"]

    schema = {
        "summary": "Short project planning summary",
        "tasks": [
            {
                "id": "TASK-001",
                "title": "Implement login API",
                "area": "backend",
                "description": "What needs to be done",
                "depends_on": [],
                "acceptance_criteria": ["Clear measurable outcome"],
            }
        ],
    }

    prompt=f"""
    You are an Experienced software project manager
    Your responsibility is to analyze the user's project idea and break it into clear development tasks.
    
    
    Project requirement:
    {requirement}
    Instructions:
    1. Understand the project requirement.
    2.Divide it into logical modules. 
    3.Arrange tasks in development order.
    4. Mention backend, frontend and database tasks if needed.
    5.Include testing tasks.
    6.Keep the tasks concise.
    7.Return valid JSON only.
    8.Use exactly this JSON shape:
    {json_prompt_schema(schema)}
    """
    response = invoke_agent_llm(
        "manager",
        [
            HumanMessage(content=prompt)
        ],
        temperature=0.2,
        task_id=state.get("task", {}).get("id"),
        agent_run_id=state.get("current_agent_run_id"),
    )
    fallback = {
        "summary": "The manager returned unstructured planning text.",
        "tasks": [
            {
                "id": "TASK-001",
                "title": "Review manager output",
                "area": "planning",
                "description": response.content,
                "depends_on": [],
                "acceptance_criteria": ["Convert this output into structured tasks."],
            }
        ],
    }
    return {"tasks": parse_json_response(response.content, fallback)}
