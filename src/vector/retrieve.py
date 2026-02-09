# vectorstore/retrieve.py
from src.vector.mmr_doc_retriever import get_mmr_retriever
from src.vector.reranker import build_reranker


async def retrieve_context(
    *,
    question: str,
    bot_id: str,
) -> str:
    # Step 1: similarity + MMR
    mmr_retriever = await get_mmr_retriever(bot_id)

    # Step 2: re-ranking
    rerank_retriever = build_reranker(mmr_retriever)

    # Step 3: async retrieval
    docs = await rerank_retriever.aget_relevant_documents(question)

    if not docs:
        return ""

    return "\n\n".join(doc.page_content for doc in docs)
