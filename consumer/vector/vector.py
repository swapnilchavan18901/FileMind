import asyncio
from qdrant_client.models import Distance, VectorParams
from consumer.vector.qdrantdb import qdrant_client

COLLECTION_NAME = "fileMind"
VECTOR_SIZE = 1536  # example: OpenAI text-embedding-3-small

def _ensure_collection_sync():
    """Synchronous helper for ensuring collection exists"""
    collections = qdrant_client.get_collections().collections
    names = [c.name for c in collections]

    if COLLECTION_NAME in names:
        return

    qdrant_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE,
        ),
    )

async def ensure_collection():
    """Async wrapper for ensuring collection exists"""
    await asyncio.to_thread(_ensure_collection_sync)
