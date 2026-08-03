#agents/developer.py

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage 
from dotenv import load_dotenv
import os 

load_dotenv();

def developer(state):
    """
    Developer agent 

    Input :
    state["requirement"]
    state["tasks"]

    output: state["code"]
    """


    requirement=state["requirement"]
    tasks=state["tasks"]
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
8.Return only the generated code.

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
        "code":response.content
    }
