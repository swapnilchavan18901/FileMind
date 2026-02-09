# vectorstore/retriever.py
from langchain_qdrant import Qdrant
from langchain_openai import OpenAIEmbeddings
from qdrant_client import AsyncQdrantClient
from src.env import env

async def get_mmr_retriever(bot_id: str):
    client = AsyncQdrantClient(url=env.QDRANT_DB_CLUSTER_URL, api_key=env.QDRANT_DB_API_KEY)

    vectorstore = Qdrant(
        client=client,
        collection_name="documents",
        embedding=OpenAIEmbeddings(),
    )

    return vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 6,          # final candidates BEFORE rerank
            "fetch_k": 25,   # similarity pool
            "filter": {
                "bot_id": bot_id
            }
        }
    )
