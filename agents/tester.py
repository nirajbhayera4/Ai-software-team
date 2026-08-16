#agents/tester.py

from langchain_core.messages import HumanMessage

from agents.llm import create_chat_model
from agents.structured_output import json_prompt_schema, parse_json_response

def tester(state):
    """
    Tester agent 
    Reads: 
    state["requirement"]
    state["implementation"]
    state["tasks"]
    state["review"]
    
    Writes:
    state["test_plan"]
    """
    
    requirement=state["requirement"]
    implementation=state["implementation"]
    tasks=state["tasks"]
    review=state["review"]
    schema = {
        "functional": [
            {
                "name": "valid login",
                "steps": ["Submit valid credentials"],
                "expected_result": "Access token is returned",
            }
        ],
        "unit": ["Unit test description"],
        "integration": ["Integration test description"],
        "edge_cases": ["Edge case description"],
        "negative": ["Negative test description"],
        "performance": ["Performance test description"],
        "security": ["Security test description"],
    }
    
    prompt=f"""
    You are an experinced software QA tester.
    
    Your job is to generate a complete testing plan for the given project.
    POROJECT REQUIREMENT;
    {
        requirement
    }
    
    TASKS:
    {
        tasks
    }
    DEVELOPER STRUCTURED OUTPUT:
    {
    implementation
    
    
    }
    CODE REVIEW :
    {
        review
    }
    generate :
    1.Functional test cases.
    2.unit test cases.
    3.integration test cases .
    4.edge cases.
    5.negative test cases.
    6.performance test cases(if applicable).
    7.security test cases(if applicable).
    
    Return valid JSON only.
    Use exactly this JSON shape:
    {json_prompt_schema(schema)}
    
    
    """
    llm = create_chat_model(temperature=0.2)

    response=llm.invoke(
        [
            HumanMessage(content=prompt)
        ]
        
    )
    fallback = {
        "functional": [],
        "unit": [],
        "integration": [],
        "edge_cases": [],
        "negative": [],
        "performance": [],
        "security": [
            "The tester returned unstructured test text. Review the raw output before execution."
        ],
        "raw_output": response.content,
    }
    return {"test_plan": parse_json_response(response.content, fallback)}
