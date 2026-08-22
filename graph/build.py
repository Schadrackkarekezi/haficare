from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from graph.nodes import appointment_agent, diagnosis_agent, doctor_agent, pharmacy_agent
from graph.planner import planner_node, route_from_planner
from graph.state import ChatState


def build_graph() -> CompiledStateGraph:
    g = StateGraph(ChatState)
    g.add_node("planner", planner_node)
    g.add_node("doctor_agent", doctor_agent)
    g.add_node("pharmacy_agent", pharmacy_agent)
    g.add_node("diagnosis_agent", diagnosis_agent)
    g.add_node("appointment_agent", appointment_agent)

    g.set_entry_point("planner")
    g.add_conditional_edges(
        "planner",
        route_from_planner,
        {
            "doctor": "doctor_agent",
            "pharmacy": "pharmacy_agent",
            "diagnosis": "diagnosis_agent",
            "appointment": "appointment_agent",
            "end": END,
        },
    )
    for node in ("doctor_agent", "pharmacy_agent", "diagnosis_agent", "appointment_agent"):
        g.add_edge(node, END)

    return g.compile(checkpointer=MemorySaver())
