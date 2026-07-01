from dotenv import load_dotenv
load_dotenv()

import os
import json
import re
from groq import Groq

_client = None

def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError("Set GROQ_API_KEY in .env")
        _client = Groq(api_key=api_key)
    return _client


ROUTER_PROMPT = """
You are a routing agent for an automotive sensor intelligence system.

Decide which tool to use to answer the user's question.

TOOLS:
1. api_tool → queries a structured SQLite database via FastAPI
   Use for: driver comparisons, session counts, RPM, speed, aggressive events, 
   vehicle info, fuel level, throttle, steering angle, battery voltage

   AVAILABLE ENDPOINTS (use exact names):
   - get_drivers           → list all drivers and vehicles
   - compare_drivers       → compare RPM, speed, throttle, aggression across drivers
   - most_aggressive       → find most aggressive driver by event count
   - get_driver_sessions   → sessions for a specific driver (needs driver_id: D001, D002, D003)
   - sessions_by_label     → filter sessions by label (aggressive or moderate)

2. rag_tool → semantic search over OBD-II technical documents
   Use for: what a sensor reading means, why a fault occurs, mechanical explanations,
   technical definitions, diagnostic advice

RESPOND ONLY with valid JSON, no other text:
{
  "route": "api" | "rag" | "both",
  "reasoning": "one sentence explaining why",
  "api_params": {"endpoint": "exact_endpoint_name", "driver_id": "D001"} | null,
  "rag_params": {"query": "..."} | null
}
"""

def route(question: str) -> dict:
    client = _get_client()

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": ROUTER_PROMPT},
                {"role": "user", "content": question}
            ],
            temperature=0,
        )
        raw = response.choices[0].message.content.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        return json.loads(raw)

    except json.JSONDecodeError:
        return {
            "route": "rag",
            "reasoning": "Routing failed, defaulting to RAG",
            "api_params": None,
            "rag_params": {"query": question},
        }