#agents/reviewer.py
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
def reviewer(state):

    """
    Reviewer agent 
    Reads:
    state["requirement"]
    state["tasks"]
    state["code"]
    
    Writes:
    state["review"]
    
    """
    requirement=state["requirement"]
    tasks=state["tasks"]
    code=state["code"]
    prompt=f"""
    You are a senior software engineer performing a professional code review.
    Your goal is to review the developer's code.
    PROJECT REQUIREMENT:
    {requirement}
    
    TASKS LIST :
    {tasks}
    GENERATED CODE:
    {code}
    
    
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
    
    Return your review in this format:
    Overall Rarting: x/10
    
    Strengths:
    -...
    
    Problems Found:
    -...
    
    Suggestions:
    -...
    
    Do NOT rewrite the code. 
    Only provide the review.
    
    """
    Response=llm.invoke(
        [
            HumanMessage(content=prompt)
        ]
    )
    return {
        "review":Response.content
    }
    