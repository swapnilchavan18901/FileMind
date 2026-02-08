import pika
import os
from src.env import env

RABBIT_MQ_URL = env.RABBIT_MQ_URL

def get_connection():
    params = pika.URLParameters(RABBIT_MQ_URL)
    return pika.BlockingConnection(params)
