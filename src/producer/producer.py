import json
import pika
from src.producer.rabbit_mq import get_connection

QUEUE = "document_process_queue"

def publish_document_job(document_id: str, bot_id: str, user_id: str):
    connection = get_connection()
    channel = connection.channel()

    # Declare durable queue
    channel.queue_declare(
        queue=QUEUE,
        durable=True
    )

    payload = {
        "document_id": document_id,
        "bot_id": bot_id,
        "user_id": user_id
    }

    channel.basic_publish(
        exchange="",              # default exchange
        routing_key=QUEUE,         # queue name
        body=json.dumps(payload),
        properties=pika.BasicProperties(
            delivery_mode=2        # persistent
        )
    )

    connection.close()
    print("📨 Job published:", payload)


if __name__ == "__main__":
    publish_document_job(
        document_id="doc-123",
        bot_id="bot-456",
        user_id="user-789"
    )
