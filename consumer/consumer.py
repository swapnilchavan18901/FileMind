import json
import asyncio
import aio_pika
import os
from botocore.exceptions import ClientError

from consumer.aws.file_loader import load_pdf_from_s3
from consumer.vector.insert import embed_and_store
from consumer.consumer_db import prisma
from consumer.consumer_env import env

RABBIT_MQ_URL = env.RABBIT_MQ_URL
QUEUE = "document_process_queue"


async def process_document(payload: dict):
    """
    Your business logic (ASYNC SAFE)
    """
    print("⚙️ Processing document:", payload)

    document_id = payload.get("document_id")
    bot_id = payload.get("bot_id")
    user_id = payload.get("user_id")

    document = await prisma.document.find_first(
        where={"id": document_id}
    )
    print(f"documentishere { document }")
    if not document:
        print(f"❌ Document not found in database: {document_id}")
        raise Exception(f"Document not found: {document_id}")

    document_path = document.storageUrl
    print(f"📄 Loading document from S3: {document_path}")

    # Async loading from S3 - returns (docs, temp_file_path)
    document_data, temp_file_path = await load_pdf_from_s3(document_path)

    try:
        # Async embedding and storage
        await embed_and_store(
            docs=document_data,
            bot_id=bot_id,
            doc_id=document_id,
            file_name=document.fileName,
            user_id=user_id,
        )

        print("✅ Done:", payload)
    finally:
        # Clean up temporary file after processing is complete
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
            print(f"🗑️  Cleaned up temp file: {temp_file_path}")


async def on_message(message: aio_pika.IncomingMessage):
    """
    Handle incoming messages with proper error handling.
    Non-recoverable errors (404, document not found, corrupted files) will NOT be requeued.
    """
    should_requeue = False
    
    try:
        payload = json.loads(message.body)
        await process_document(payload)
        # ACK happens automatically if no exception
        await message.ack()
        
    except ClientError as e:
        # S3 errors - check if it's a 404 (file not found)
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == '404' or '404' in str(e):
            print(f"❌ File not found in S3 (404). Not requeuing. Error: {e}")
            # Don't requeue - file doesn't exist
            await message.reject(requeue=False)
        else:
            print(f"⚠️ S3 error (will retry): {e}")
            should_requeue = True
            await message.reject(requeue=True)
            
    except ValueError as e:
        # ValueError is used for validation errors (empty PDFs, no text content, etc.)
        error_msg = str(e)
        print(f"❌ Validation error. Not requeuing. Error: {error_msg}")
        await message.reject(requeue=False)
        
    except Exception as e:
        error_msg = str(e).lower()
        # Check for non-recoverable errors
        if "not found" in error_msg:
            print(f"❌ Resource not found. Not requeuing. Error: {e}")
            await message.reject(requeue=False)
        elif any(x in error_msg for x in ["invalid pdf", "pdf header", "eof marker", "stream has ended unexpectedly"]):
            print(f"❌ Corrupted or invalid PDF file. Not requeuing. Error: {e}")
            print(f"⚠️  The file in S3 is corrupted. Check your upload process!")
            await message.reject(requeue=False)
        elif any(x in error_msg for x in ["empty update request", "no extractable text"]):
            print(f"❌ PDF has no text content (likely scanned/image-based). Not requeuing. Error: {e}")
            print(f"⚠️  Consider implementing OCR for scanned PDFs!")
            await message.reject(requeue=False)
        else:
            print(f"⚠️ Error processing message (will retry): {e}")
            should_requeue = True
            await message.reject(requeue=True)


async def start_consumer():
    # Connect to Prisma before starting consumer
    print("🔌 Connecting to Prisma...")
    await prisma.connect()
    print("✅ Prisma connected")

    try:
        connection = await aio_pika.connect_robust(RABBIT_MQ_URL)

        async with connection:
            channel = await connection.channel()

            # Process ONE message at a time (important)
            await channel.set_qos(prefetch_count=1)

            queue = await channel.declare_queue(
                QUEUE,
                durable=True
            )

            await queue.consume(on_message)

            print("👂 Async consumer started. Waiting for messages...")
            await asyncio.Future()  # run forever
    finally:
        # Disconnect Prisma when shutting down
        print("🔌 Disconnecting Prisma...")
        await prisma.disconnect()
        print("✅ Prisma disconnected")


if __name__ == "__main__":
    asyncio.run(start_consumer())
