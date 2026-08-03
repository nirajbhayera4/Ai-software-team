from typing import TypedDict

from langgraph.graph import END, StateGraph
from agents.manager import manager

from agents.developer import developer
from agents.reviewer import reviewer
from agents.tester import tester


class AgentState(TypedDict, total=False):
    requirement: str
    tasks: str
    code: str
    review: str
    tests: str
    documentation: str


# creating the graph
builder = StateGraph(AgentState)

#==========
# add the nodes
#==========

builder.add_node("manager", manager)
builder.add_node("developer", developer)
builder.add_node("reviewer", reviewer)
builder.add_node("tester", tester)


# set the entry point
builder.set_entry_point("manager")


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

# compile the graph
graph = builder.compile()

