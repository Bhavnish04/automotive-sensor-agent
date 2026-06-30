from dotenv import load_dotenv
load_dotenv()

import os
import hashlib
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

COLLECTION_NAME = "obd_documents"
EMBEDDING_MODEL  = "all-MiniLM-L6-v2"
VECTOR_DIM       = 384
CHUNK_SIZE       = 400
CHUNK_OVERLAP    = 80

splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    length_function=len,
)


def get_client() -> QdrantClient:
    url = os.environ.get("QDRANT_URL")
    api_key = os.environ.get("QDRANT_API_KEY")
    if not url or not api_key:
        raise EnvironmentError("Set QDRANT_URL and QDRANT_API_KEY in .env")
    return QdrantClient(url=url, api_key=api_key)


def ensure_collection(client: QdrantClient) -> None:
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
        )
        print(f"✅ Created collection: {COLLECTION_NAME}")
    else:
        print(f"ℹ️  Collection already exists: {COLLECTION_NAME}")


def ingest_pdfs(pdf_dir: str) -> int:
    model = SentenceTransformer(EMBEDDING_MODEL)
    client = get_client()
    ensure_collection(client)

    pdf_paths = list(Path(pdf_dir).glob("*.pdf"))
    if not pdf_paths:
        print(f"⚠️  No PDFs found in {pdf_dir}")
        return 0

    print(f"Found {len(pdf_paths)} PDF(s)")
    total_points = 0

    for pdf_path in pdf_paths:
        print(f"\n📄 Processing: {pdf_path.name}")

        # LangChain loads + splits the PDF into page-level documents
        loader = PyPDFLoader(str(pdf_path))
        documents = loader.load()  # one Document per page

        points = []
        for doc in documents:
            page_num = doc.metadata.get("page", 0) + 1  # LangChain pages are 0-indexed
            chunks = splitter.split_text(doc.page_content)

            for chunk_idx, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue

                vector = model.encode(chunk).tolist()
                raw_id = f"{pdf_path.name}_{page_num}_{chunk_idx}"
                point_id = int(hashlib.md5(raw_id.encode()).hexdigest(), 16) % (2**63)

                points.append(PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "text": chunk,
                        "filename": pdf_path.name,
                        "page": page_num,
                    }
                ))

        if points:
            client.upsert(collection_name=COLLECTION_NAME, points=points)
            print(f"  ✅ Upserted {len(points)} chunks")
            total_points += len(points)

    return total_points


if __name__ == "__main__":
    n = ingest_pdfs("data")
    print(f"\n🎉 Done. Total chunks: {n}")