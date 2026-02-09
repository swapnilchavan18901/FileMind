from src.vector.client import qdrant_client
from openai import AsyncOpenAI
from src.env import env

openai_client = AsyncOpenAI(api_key=env.OPENAI_API_KEY)


async def embed_text(text: str) -> list[float]:
    response = await openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    print(f"responseishere{response}")
    return response.data[0].embedding

async def retrieve_relevant_chunks(
    collection_name: str,
    question: str,
    top_k: int = 5
):
    print("retrieving relevant chunks")
    # 1. Embed the question
    query_vector = await embed_text(question)
    print(f"queryvectorishere{len(query_vector)}")
    
    # 2. Search Qdrant
    print(f"collectionnameishere{collection_name}")
    results = await qdrant_client.query_points(
        collection_name=collection_name,
        query=query_vector,
    )

    # 3. Extract chunk text
    # chunks = []
    # for r in results:
    #     chunks.append({
    #         "score": r.score,
    #         "text": r.payload.get("text"),
    #         "metadata": r.payload
    #     })
    # print(f"chunksishere{chunks}")
    return results
