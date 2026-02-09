from dotenv import load_dotenv
load_dotenv() 

from fastapi import FastAPI
from src.routes.auth import router as auth_router
from src.db import prisma
from src.routes.bots import router as bots_router
from src.routes.api_key import router as api_key_router
from src.sockets.ws_chats import socket_app
from src.routes.documenation import router as documentation_router
# from src.routes.testing import router as testing_router
app = FastAPI()

@app.on_event("startup")
async def startup():
    await prisma.connect()

@app.on_event("shutdown")
async def shutdown():
    await prisma.disconnect()
    
#sockets


app.include_router(auth_router)
app.include_router(bots_router)
app.include_router(api_key_router)
app.include_router(documentation_router)
# app.include_router(testing_router)
app.mount("/", socket_app)