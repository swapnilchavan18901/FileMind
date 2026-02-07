from fastapi import FastAPI
from src.routes.auth import router as auth_router
from dotenv import load_dotenv
load_dotenv() 
from src.db import prisma
app = FastAPI()
@app.on_event("startup")
async def startup():
    await prisma.connect()

@app.on_event("shutdown")
async def shutdown():
    await prisma.disconnect()
    
app.include_router(auth_router)
