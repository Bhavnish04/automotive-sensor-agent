from dotenv import load_dotenv
load_dotenv()

import os
import json
from typing import TypedDict
from langgraph.graph import StateGraph, END
from agent.router import route
from agent.tools import api_tool, rag_tool
from google import genai


class AgentState(TypedDict):
    question:       str
    route:          str
    routing_reason: str
    api_params:     dict | None    
    rag_params:     dict | None    
    api_result:     str | None
    rag_result:     str | None
    final_answer:   str


def router_node(state: AgentState) -> AgentState:   #4
    decision = route(state["question"])
    return {
        **state,
        "route":          decision.get("route", "rag"),
        "routing_reason": decision.get("reasoning", ""),
        "api_params":     decision.get("api_params"),
        "rag_params":     decision.get("rag_params"),
    }


def api_node(state: AgentState) -> AgentState:           #6
    params = state.get("api_params") or {}
    endpoint = params.get("endpoint", "compare_drivers")
    driver_id = params.get("driver_id", "")
    
    result = api_tool(endpoint, {"driver_id": driver_id})
    return {**state, "api_result": json.dumps(result)}


def rag_node(state: AgentState) -> AgentState:               #7
    result = rag_tool(state["question"])
    return {**state, "rag_result": json.dumps(result)}


def synthesizer_node(state: AgentState) -> AgentState:                #8
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    context = ""
    if state.get("api_result"):
        context += f"DATABASE RESULT:\n{state['api_result']}\n\n"
    if state.get("rag_result"):
        context += f"DOCUMENT RESULT:\n{state['rag_result']}\n\n"

    prompt = f"""You are an automotive sensor data assistant.
Question: {state['question']}
Data: {context}
Answer the question clearly based on the data provided."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return {**state, "final_answer": response.text.strip()}


def build_graph():   #3
    graph = StateGraph(AgentState)

    graph.add_node("router",      router_node)
    graph.add_node("api",         api_node)
    graph.add_node("rag",         rag_node)
    graph.add_node("synthesizer", synthesizer_node)

    graph.set_entry_point("router")

    # After router — decide which tool to call first       #5
    graph.add_conditional_edges(
        "router",
        lambda s: s["route"],
        {
            "api":  "api",
            "rag":  "rag",
            "both": "api",
        }
    )

    # After api — if route is 'both' go to rag too, else go straight to synthesizer
    graph.add_conditional_edges(
        "api",
        lambda s: "rag" if s["route"] == "both" else "synthesizer",
        {
            "rag":         "rag",
            "synthesizer": "synthesizer",
        }
    )

    graph.add_edge("rag", "synthesizer")
    graph.add_edge("synthesizer", END)

    return graph.compile()


def ask(question: str) -> dict:  #2
    graph = build_graph()
    result = graph.invoke({
        "question":       question,
        "route":          "",
        "routing_reason": "",
        "api_params":     None,
        "rag_params":     None,
        "api_result":     None,
        "rag_result":     None,
        "final_answer":   "",
    })                                        #9
    return {
        "final_answer":   result["final_answer"],
        "route":          result["route"],
        "routing_reason": result["routing_reason"],
    }