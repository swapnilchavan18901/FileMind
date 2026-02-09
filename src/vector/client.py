# vectorstore/client.py
from qdrant_client import AsyncQdrantClient
from src.env import env
def get_qdrant_client():
    return AsyncQdrantClient(
        url=env.QDRANT_DB_CLUSTER_URL,
        api_key=env.QDRANT_DB_API_KEY,
    )
