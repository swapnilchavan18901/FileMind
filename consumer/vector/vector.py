import asyncio
from qdrant_client.models import Distance, VectorParams
from consumer.vector.qdrantdb import qdrant_client, collection_exists

VECTOR_SIZE = 1536  # example: OpenAI text-embedding-3-small

def _ensure_collection_sync(bot_id: str):
    """Synchronous helper for ensuring collection exists based on bot_id"""
    # Use bot_id directly as collection name (UUID)
    if collection_exists(bot_id):
        print(f"✅ Collection '{bot_id}' already exists")
        return
    
    print(f"📦 Creating new collection '{bot_id}'...")
    qdrant_client.create_collection(
        collection_name=bot_id,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE,
        ),
    )
    print(f"✅ Collection '{bot_id}' created successfully")

async def ensure_collection(bot_id: str):
    """Async wrapper for ensuring collection exists based on bot_id"""
    await asyncio.to_thread(_ensure_collection_sync, bot_id)
