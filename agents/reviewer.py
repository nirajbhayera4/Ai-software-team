from langchain_core.messages import HumanMessage

from agents.llm import invoke_agent_llm
from agents.structured_output import json_prompt_schema, parse_json_response

def reviewer(state):

    """
    Reviewer agent 
    Reads:
    state["requirement"]
    state["tasks"]
    state["implementation"]
    
    Writes:
    state["review"]
    
    """
    requirement=state["requirement"]
    tasks=state["tasks"]
    implementation=state["implementation"]
    schema = {
        "overall_rating": 8,
        "approved": False,
        "strengths": ["What is working well"],
        "issues": [
            {
                "severity": "medium",
                "file": "src/auth/login.py",
                "description": "Problem found",
                "suggestion": "How to fix it",
            }
        ],
        "missing_functionality": ["Missing requirement"],
        "security_concerns": ["Security concern"],
        "suggestions": ["Improvement suggestion"],
    }
    prompt=f"""
    You are a senior software engineer performing a professional code review.
    Your goal is to review the developer's code.
    PROJECT REQUIREMENT:
    {requirement}
    
    TASKS LIST :
    {tasks}
    DEVELOPER STRUCTURED OUTPUT:
    {implementation}
    
    
    Review the code based on the following:
    1.Correctness
    2.code quality
    3.Readabality
    4.PEP8 compliance
    5.Error handling 
    6.Performance
    7.security concerns 
    8. Missing functionality
    9.Best practices 
    10.Scalability
    
    Return valid JSON only.
    Use exactly this JSON shape:
    {json_prompt_schema(schema)}
    
    """
    Response = invoke_agent_llm(
        "reviewer",
        [
            HumanMessage(content=prompt)
        ],
        temperature=0.2,
        task_id=state.get("task", {}).get("id"),
        agent_run_id=state.get("current_agent_run_id"),
    )
    fallback = {
        "overall_rating": 0,
        "approved": False,
        "strengths": [],
        "issues": [
            {
                "severity": "high",
                "file": "",
                "description": "The reviewer returned unstructured review text.",
                "suggestion": Response.content,
            }
        ],
        "missing_functionality": [],
        "security_concerns": [],
        "suggestions": [],
    }
    return {"review": parse_json_response(Response.content, fallback)}
