from langchain_core.messages import HumanMessage 
from agents.llm import create_chat_model

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
    llm = create_chat_model(temperature=0.2)

    response=llm.invoke(
        [
            HumanMessage(content=prompt)
        ]
    )
    return {
        "tasks": response.content
    }
    

    
    
