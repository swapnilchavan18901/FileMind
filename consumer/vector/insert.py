# ingestion/chunk_embed.py

import uuid
import asyncio
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from qdrant_client.models import PointStruct
from consumer.vector.qdrantdb import qdrant_client
from consumer.consumer_env import env

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=env.OPENAI_API_KEY,
)
QDRANT_COLLECTION = "fileMind"

def _embed_and_store_sync(
    docs,
    bot_id: str,
    doc_id: str,
    file_name: str,
    user_id: str
):
    """Synchronous helper for embedding and storing"""
    # Don't print the entire document list - it's too long
    print(f"📚 Processing {len(docs)} pages from '{file_name}'")
    
    # Check if documents have any content
    pages_with_content = sum(1 for doc in docs if doc.page_content and doc.page_content.strip())
    print(f"   Pages with content: {pages_with_content}/{len(docs)}")
    
    if pages_with_content == 0:
        error_msg = (
            f"PDF '{file_name}' has no extractable text content. "
            f"This is likely a scanned/image-based PDF. "
            f"Please use OCR or upload a text-based PDF."
        )
        print(f"❌ {error_msg}")
        raise ValueError(error_msg)
    
    # Filter out empty pages before splitting
    docs_with_content = [doc for doc in docs if doc.page_content and doc.page_content.strip()]
    print(f"   Splitting {len(docs_with_content)} non-empty pages into chunks...")
    
    chunks = splitter.split_documents(docs_with_content)
    print(f"   ✅ Created {len(chunks)} chunks")
    
    if not chunks:
        raise ValueError(f"No chunks created from document '{file_name}'. Document may be empty.")
    
    print(f"   🔄 Generating embeddings for {len(chunks)} chunks...")
    texts = [c.page_content for c in chunks]
    vectors = embeddings.embed_documents(texts)
    print(f"   ✅ Embeddings generated")

    print(f"   📦 Preparing {len(chunks)} points for Qdrant...")
    points = []
    for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "bot_id": bot_id,
                    "doc_id": doc_id,
                    "file_name": file_name,
                    "user_id": user_id,
                    "page": chunk.metadata.get("page"),
                    "chunk_index": i,
                    "text": chunk.page_content
                }
            )
        )

    # Batch upsert for better performance and to avoid timeouts
    print(f"   💾 Upserting {len(points)} points to Qdrant in batches...")
    batch_size = 100
    total_batches = (len(points) + batch_size - 1) // batch_size
    
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        print(f"      Batch {batch_num}/{total_batches}: Upserting {len(batch)} points...")
        qdrant_client.upsert(
            collection_name=QDRANT_COLLECTION,
            points=batch
        )
    
    print(f"✅ Successfully stored {len(points)} chunks in Qdrant")

async def embed_and_store(
    docs,
    bot_id: str,
    doc_id: str,
    file_name: str,
    user_id: str
):
    """Async wrapper for embedding and storing using thread pool"""
    await asyncio.to_thread(
        _embed_and_store_sync,
        docs,
        bot_id,
        doc_id,
        file_name,
        user_id
    )
