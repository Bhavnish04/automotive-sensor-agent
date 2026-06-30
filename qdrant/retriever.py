from dotenv import load_dotenv
load_dotenv()

import os
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

COLLECTION_NAME = "obd_documents"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

_model = None
_client = None


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def _get_client():
    global _client
    if _client is None:
        url = os.environ.get("QDRANT_URL")
        api_key = os.environ.get("QDRANT_API_KEY")
        _client = QdrantClient(url=url, api_key=api_key)
    return _client


def retrieve(query: str, top_k: int = 5) -> list[dict]:
    model = _get_model()
    client = _get_client()
    
    vector = model.encode(query).tolist()
    
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=vector,
        limit=top_k,
    )
    
    return [
        {
            "text": hit.payload["text"],
            "filename": hit.payload["filename"],
            "page": hit.payload["page"],
            "score": hit.score,
        }
        for hit in results.points
    ]