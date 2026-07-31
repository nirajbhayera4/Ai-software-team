#agents/tester.py

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage 
from dotenv import load_dotenv
import os 

load_dotenv();

#initialize the LLM
llm=ChatOpenAI(
    model="gpt-4.1 -mini",
    temperature=0.2,
)
def tester(state):
    """
    Tester agent 
    Reads: 
    state["requirement"]
    state["code"]
    state["tasks"]
    state["review"]
    
    Writes:
    state["tests"]
    """
    
    requirement=state["requirement"]
    code=state["code"]
    tasks=state["tasks"]
    review=state["review"]
    
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
    GENERATED CODE:
    {
    code 
    
    
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
    
    Return your response in the following format :
    ===================
    FUCNTIONAL TEST CASES
    ===================
    -test 1
    -test 2
    ===================
    UNIT TESTS
    ===================
    -test 1
    -test 2
    
    ===================
    EDGE CASES
    ===================
    -case 1 
    -case 2
    
    ===================
    NEGATIVE TEST CASES
    ===================
    -test 1
    -test 2
    
    ===================
    PERFORMANCE TEST CASES
    ===================
    -...
    
    ===================
    SECURITY TEST CASES
    ===================
    -...
    
    Only return the testing plan.
    Do not explain the testing plan.
    
    
    """
    response=llm.invoke(
        [
            HumanMessage(content=prompt)
        ]
        
    )
    return {
        "tests":response.content
    }
    
    