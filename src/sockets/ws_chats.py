import socketio

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
)

socket_app = socketio.ASGIApp(sio)

# 👇 IMPORT HANDLERS SO EVENTS REGISTER
from src.sockets import handlers
