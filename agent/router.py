from dotenv import load_dotenv
load_dotenv()
import os
import json
import re
from google import genai

_client = None

def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "Set GEMINI_API_KEY. Get one free at https://aistudio.google.com"
            )
        _client = genai.Client(api_key=api_key)
    return _client


ROUTER_PROMPT = """
You are a routing agent for an automotive sensor intelligence system.

Decide which tool to use to answer the user's question.

TOOLS:
1. api_tool → queries a structured SQLite database via FastAPI
   Use for: driver comparisons, session counts, RPM, speed, aggressive events, 
   vehicle info, fuel level, throttle, steering angle, battery voltage

2. rag_tool → semantic search over OBD-II technical documents
   Use for: what a sensor reading means, why a fault occurs, mechanical explanations,
   technical definitions, diagnostic advice

RESPOND ONLY with valid JSON, no other text:
{
  "route": "api" | "rag" | "both",
  "reasoning": "one sentence explaining why",
  "api_params": {"endpoint": "...", "driver_id": "..."} | null,
  "rag_params": {"query": "..."} | null
}
"""

def route(question: str) -> dict:
    client = _get_client()
    
    prompt = f"{ROUTER_PROMPT}\n\nUser question: {question}"
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        raw = response.text.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        return json.loads(raw)
    
    except json.JSONDecodeError as e:
        return {
            "route": "rag",
            "reasoning": f"Routing failed, defaulting to RAG",
            "api_params": None,
            "rag_params": {"query": question},
        }