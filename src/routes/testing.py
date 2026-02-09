import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.db import prisma
from src.llm.llm_run import run_chat
from src.vector.retrieve import retrieve_context

router = APIRouter(tags=["testing"])

class TestingRequest(BaseModel):
    question: str

@router.post("/testing/{bot_id}")
async def testing(
    bot_id: str,
    request: TestingRequest,
):
    bot = await prisma.bot.find_unique(
        where={"id": bot_id}
    )
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
        
    context = await retrieve_context(
        question=request.question,
        bot_id=bot_id
    )

    answer = await run_chat(
        question=request.question,
        context=context,
        bot_system_prompt=bot.systemPrompt
    )

    return {
        "message": answer,
    }
