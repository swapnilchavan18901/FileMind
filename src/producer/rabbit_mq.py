import aio_pika
import os
from src.env import env

RABBIT_MQ_URL = env.RABBIT_MQ_URL

async def get_connection():
    connection = await aio_pika.connect_robust(RABBIT_MQ_URL)
    return connection
