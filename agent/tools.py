from dotenv import load_dotenv
load_dotenv()

import httpx
import json

API_BASE = "http://localhost:8000"


def api_tool(endpoint: str, params: dict = {}) -> dict:
    """Call the FastAPI structured database."""
    
    endpoint_map = {
        "get_drivers":           "/drivers",
        "get_driver_sessions":   "/drivers/{driver_id}/sessions",
        "most_aggressive":       "/drivers/aggressive",
        "sessions_by_label":     "/sessions/{label}",
        "compare_drivers":       "/compare",
    }
    
    if endpoint not in endpoint_map:
        return {"error": f"Unknown endpoint '{endpoint}'"}
    
    url = API_BASE + endpoint_map[endpoint]
    
    # Fill in path parameters
    for key, value in params.items():
        url = url.replace(f"{{{key}}}", str(value))
    
    try:
        response = httpx.get(url, timeout=10.0)
        if response.status_code == 200:
            return response.json()
        return {"error": f"API returned {response.status_code}"}
    
    except httpx.ConnectError:
        return {"error": "Cannot connect to API. Make sure FastAPI is running."}
    except Exception as e:
        return {"error": str(e)}
    
    
    
def rag_tool(query: str) -> dict:
    """Semantic search over OBD-II technical documents in Qdrant."""
    # Stub for now — Qdrant setup comes in next phase
    return {
        "message": "RAG tool not yet configured. Qdrant setup pending.",
        "query": query
    }