#agents/manager.py
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage 
from dotenv import load_dotenv
import os 

load_dotenv();

def manager(state):
    """
    Manager agent 
    Input : state["requirement"]
    
    output: state["tasks"]
    
    
    
    """
    requirement=state["requirement"]
    
    
    
    prompt=f"""
    You are an Experienced software project manager
    Your responsibility is to analyze the user's project idea and break it into clear development tasks.
    
    
    Project requirement:
    {requirement}
    Instructions :
    1. Understand the project requirement.
    2.Divide it into logical modules. 
    3.Arrange tasks in development order.
    4. Mention backend, frontend and database tasks if needed.
    5.Include testing tasks.
    6.Keep the tasks concise.
    7.Return only the numbered tasks list.
    """
    llm = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0.2,
    )

    response=llm.invoke(
        [
            HumanMessage(content=prompt)
        ]
    )
    return {
        "tasks": response.content
    }
    

    
    
