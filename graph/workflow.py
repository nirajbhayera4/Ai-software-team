from langgraph.graph import StateGraph, END
from state import AgentState
from agents.manager import manager

from agents.developer import developer
from agents.reviewer import reviewer
from agents.tester import tester

#creating the graph 
builder=StateGraph(AgentState)

#==========
#add the nodes 
#==========

build.add_node("manager", manager);
build.add_node("developer", developer);
build.add_node("reviewer", reviewer);
build.add_node("tester", tester);


#set the entry point 
build.set_entry_point("manager")


#create the workflow 
builder.add_edge(
    "manager",
    "developer"
)

builder.add_edge(
    "developer",
    "reviewer"
)

builder.add_edge(
    "reviewer",
    "tester"
)

builder.add_edge(
    "tester",
    END
)

#compile the graph 
graph=builder.compile()

