from src.vector.client import qdrant_client
from openai import AsyncOpenAI
from src.env import env

openai_client = AsyncOpenAI(api_key=env.OPENAI_API_KEY)


async def embed_text(text: str) -> list[float]:
    response = await openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

async def retrieve_relevant_chunks(
    collection_name: str,
    question: str,
    top_k: int = 5
):
    # 1. Embed the question
    query_vector = await embed_text(question)
    
    # 2. Search Qdrant
    results = qdrant_client.query_points(
        collection_name=collection_name,
        query=query_vector,
    )

    # 3. Extract only relevant data for AI
    relevant_data = []
    for point in results.points:
        relevant_data.append({
            "text": point.payload.get("text"),
            "score": point.score,
            "file_name": point.payload.get("file_name"),
            "page": point.payload.get("page")
        })
    
    return relevant_data
